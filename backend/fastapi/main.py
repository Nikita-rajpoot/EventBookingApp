import base64, io, os, uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx, jwt, qrcode
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from passlib.context import CryptContext
from pydantic import BaseModel, Field

load_dotenv()
DB_NAME = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/evently').rsplit('/', 1)[-1].split('?')[0] or 'evently'
client = AsyncIOMotorClient(os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/evently'))
db = client[DB_NAME]
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
app = FastAPI(title='TaeVerse API', version='1.0.0')
origins = [v.strip() for v in os.getenv('CLIENT_ORIGIN', '*').split(',')]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def oid(value: str):
    try: return ObjectId(value)
    except Exception: raise HTTPException(400, 'Invalid ID')
def clean(value: Any):
    if isinstance(value, ObjectId): return str(value)
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, list): return [clean(v) for v in value]
    if isinstance(value, dict): return {k: clean(v) for k, v in value.items()}
    return value
def token(user: dict): return jwt.encode({'id': str(user['_id']), 'role': user['role'], 'exp': datetime.now(timezone.utc)+timedelta(days=7)}, os.getenv('JWT_SECRET','dev-secret'), algorithm='HS256')
def public_user(user: dict): return {'id':str(user['_id']), 'name':user['name'], 'email':user['email'], 'role':user.get('role','user')}
async def current(request: Request):
    value=request.headers.get('Authorization','').removeprefix('Bearer ').strip()
    try: data=jwt.decode(value, os.getenv('JWT_SECRET','dev-secret'), algorithms=['HS256']); user=await db.users.find_one({'_id':oid(data['id'])})
    except Exception: user=None
    if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'Authentication required')
    return user
async def admin(user=Depends(current)):
    if user.get('role')!='admin': raise HTTPException(status.HTTP_403_FORBIDDEN, 'Admin access required')
    return user
class Auth(BaseModel): email:str; password:str
class Register(Auth): name:str; role: str='user'
class BookingIn(BaseModel): eventId:str; ticketType:str; quantity:int=Field(gt=0); seatNumbers:list[str]=[]
class ReviewIn(BaseModel): rating:int=Field(ge=1,le=5); comment:str=''
class CouponIn(BaseModel): code:str; amount:float; eventId:Optional[str]=None
class MessageIn(BaseModel): message:str=Field(min_length=1,max_length=1000)

@app.get('/health')
async def health(): return {'status':'ok'}
@app.post('/api/auth/register', status_code=201)
async def register(body:Register):
    if body.role not in ('user','organizer'): raise HTTPException(400,'Invalid role')
    if await db.users.find_one({'email':body.email.lower()}): raise HTTPException(409,'Email already in use')
    user={'name':body.name.strip(),'email':body.email.lower(),'password':pwd.hash(body.password),'role':body.role,'favorites':[],'createdAt':datetime.now(timezone.utc)}
    user['_id']=(await db.users.insert_one(user)).inserted_id
    return {'user':public_user(user),'token':token(user)}
@app.post('/api/auth/login')
async def login(body:Auth):
    user=await db.users.find_one({'email':body.email.lower()})
    if not user or not pwd.verify(body.password,user.get('password','')): raise HTTPException(401,'Invalid credentials')
    return {'user':public_user(user),'token':token(user)}
@app.post('/api/auth/forgot-password')
async def forgot_password(): return {'message':'If the email exists, a reset link has been sent.'}

@app.get('/api/events')
async def events(): return clean(await db.events.find().sort('date',1).to_list(None))
@app.get('/api/events/discover/ticketmaster')
async def ticketmaster(request:Request):
    key=os.getenv('TICKETMASTER_API_KEY')
    if not key: raise HTTPException(503,'Ticketmaster is not configured. Add TICKETMASTER_API_KEY to backend/fastapi/.env.')
    params={'apikey':key,'size':min(int(request.query_params.get('size','20')),50),'countryCode':request.query_params.get('countryCode','IN')}
    for name in ('keyword','city','classificationName','startDateTime'):
        if request.query_params.get(name): params[name]=request.query_params[name]
    async with httpx.AsyncClient(timeout=12) as http:
        response=await http.get('https://app.ticketmaster.com/discovery/v2/events.json',params=params)
    if response.status_code>=400: raise HTTPException(response.status_code,response.json().get('fault',{}).get('faultstring','Ticketmaster request failed'))
    out=[]
    for item in response.json().get('_embedded',{}).get('events',[]):
        venue=item.get('_embedded',{}).get('venues',[{}])[0]; images=sorted(item.get('images',[]),key=lambda x:x.get('width',0),reverse=True); price=(item.get('priceRanges') or [{}])[0].get('min',0)
        out.append({'_id':f"tm-{item['id']}",'title':item['name'],'category':item.get('classifications',[{}])[0].get('segment',{}).get('name','Arts'),'date':item.get('dates',{}).get('start',{}).get('localDate'),'time':item.get('dates',{}).get('start',{}).get('localTime','TBA'),'location':', '.join(filter(None,[venue.get('name'),venue.get('city',{}).get('name'),venue.get('country',{}).get('name')])), 'price':price,'image':images[0]['url'] if images else '', 'description':item.get('info') or item.get('pleaseNote') or 'Live event details from Ticketmaster.','organizer':item.get('promoter',{}).get('name','Ticketmaster'),'seats':0,'ticketTypes':[{'name':'General admission','price':price,'remaining':0}],'featured':True,'externalUrl':item.get('url'),'source':'ticketmaster'})
    return out
@app.get('/api/events/{event_id}')
async def event(event_id:str):
    item=await db.events.find_one({'_id':oid(event_id)})
    if not item: raise HTTPException(404,'Event not found')
    return clean(item)
@app.post('/api/events',status_code=201)
async def create_event(payload:dict, _=Depends(admin)):
    payload['createdAt']=datetime.now(timezone.utc); result=await db.events.insert_one(payload); payload['_id']=result.inserted_id; return clean(payload)
@app.patch('/api/events/{event_id}')
async def update_event(event_id:str,payload:dict,_=Depends(admin)):
    item=await db.events.find_one_and_update({'_id':oid(event_id)},{'$set':payload},return_document=ReturnDocument.AFTER)
    if not item: raise HTTPException(404,'Event not found')
    return clean(item)
@app.delete('/api/events/{event_id}',status_code=204)
async def delete_event(event_id:str,_=Depends(admin)): await db.events.delete_one({'_id':oid(event_id)})
@app.get('/api/events/{event_id}/seats')
async def seats(event_id:str,_=Depends(current)):
    item=await db.events.find_one({'_id':oid(event_id)},{'seatLayout':1})
    if not item: raise HTTPException(404,'Event not found')
    return clean(item.get('seatLayout',[]))
@app.post('/api/events/{event_id}/seats/lock',status_code=201)
async def lock_seats(event_id:str,payload:dict,user=Depends(current)):
    seat_ids=payload.get('seatIds',[])
    if not isinstance(seat_ids,list) or not seat_ids: raise HTTPException(400,'Select at least one seat')
    event=await db.events.find_one({'_id':oid(event_id)})
    if not event: raise HTTPException(404,'Event not found')
    available={seat.get('seatId') for seat in event.get('seatLayout',[]) if seat.get('status')=='available'}
    if any(value not in available for value in seat_ids): raise HTTPException(400,'A selected seat is unavailable')
    expires=datetime.now(timezone.utc)+timedelta(minutes=10); await db.seatlocks.delete_many({'event':event['_id'],'user':user['_id']}); await db.seatlocks.insert_many([{'event':event['_id'],'seatId':value,'user':user['_id'],'expiresAt':expires} for value in seat_ids]); return {'expiresAt':expires.isoformat()}

@app.get('/api/bookings')
async def bookings(user=Depends(current)):
    query={} if user['role']=='admin' else {'user':user['_id']}; rows=await db.bookings.find(query).sort('createdAt',-1).to_list(None)
    for row in rows: row['event']=await db.events.find_one({'_id':row['event']})
    return clean(rows)
@app.post('/api/bookings',status_code=201)
async def booking(body:BookingIn,user=Depends(current)):
    event=await db.events.find_one({'_id':oid(body.eventId)})
    if not event: raise HTTPException(404,'Event not found')
    ticket=next((x for x in event.get('ticketTypes',[]) if x['name']==body.ticketType),None)
    if not ticket or ticket.get('remaining',0)<body.quantity: raise HTTPException(400,'Tickets unavailable')
    await db.events.update_one({'_id':event['_id'],'ticketTypes.name':body.ticketType},{'$inc':{'ticketTypes.$.remaining':-body.quantity}})
    row={'bookingId':f"EV-{uuid.uuid4().hex[:8].upper()}",'user':user['_id'],'event':event['_id'],'ticketType':body.ticketType,'quantity':body.quantity,'total':ticket['price']*body.quantity,'seatNumbers':body.seatNumbers,'status':'confirmed','checkedIn':False,'createdAt':datetime.now(timezone.utc)}; row['_id']=(await db.bookings.insert_one(row)).inserted_id
    ticket_id=f"TK-{uuid.uuid4().hex[:8].upper()}"; payload={'ticketId':ticket_id,'bookingId':row['bookingId']}; await db.tickets.insert_one({'ticketId':ticket_id,'booking':row['_id'],'event':event['_id'],'user':user['_id'],'ticketType':body.ticketType,'qrPayload':str(payload),'status':'ACTIVE'})
    return clean({'booking':row,'ticketId':ticket_id,'qrPayload':payload})
@app.patch('/api/bookings/{booking_id}/cancel')
async def cancel(booking_id:str,user=Depends(current)):
    row=await db.bookings.find_one_and_update({'_id':oid(booking_id),'user':user['_id']},{'$set':{'status':'cancelled'}},return_document=ReturnDocument.AFTER)
    if not row: raise HTTPException(404,'Booking not found')
    await db.tickets.update_many({'booking':row['_id']},{'$set':{'status':'CANCELLED'}}); return clean(row)

@app.get('/api/favorites')
async def favorites(user=Depends(current)):
    ids=user.get('favorites',[]); return clean(await db.events.find({'_id':{'$in':ids}}).to_list(None))
@app.post('/api/favorites/{event_id}')
async def favorite(event_id:str,user=Depends(current)):
    value=oid(event_id); op={'$pull':{'favorites':value}} if value in user.get('favorites',[]) else {'$addToSet':{'favorites':value}}; await db.users.update_one({'_id':user['_id']},op); return {'ok':True}
@app.get('/api/notifications')
async def notifications(user=Depends(current)): return clean(await db.notifications.find({'user':user['_id']}).sort('createdAt',-1).to_list(None))

@app.post('/api/admin/tickets/verify')
async def verify(payload:dict,user=Depends(admin)):
    ticket=await db.tickets.find_one({'$or':[{'ticketId':payload.get('ticketId')},{'qrPayload':payload.get('qrPayload')}]})
    if not ticket: raise HTTPException(404,{'valid':False,'message':'Ticket not found'})
    if ticket['status']!='ACTIVE': raise HTTPException(409,{'valid':False,'message':'Ticket is not active'})
    await db.tickets.update_one({'_id':ticket['_id']},{'$set':{'status':'USED','checkedInAt':datetime.now(timezone.utc),'checkedInBy':user['_id']}}); await db.bookings.update_one({'_id':ticket['booking']},{'$set':{'checkedIn':True}}); return {'valid':True,'message':'Check-in complete'}
@app.get('/api/admin/stats')
async def stats(_=Depends(admin)):
    revenue=await db.bookings.aggregate([{'$match':{'status':'confirmed'}},{'$group':{'_id':None,'total':{'$sum':'$total'}}}]).to_list(1); return {'events':await db.events.count_documents({}),'users':await db.users.count_documents({}),'bookings':await db.bookings.count_documents({}),'revenue':revenue[0]['total'] if revenue else 0}

@app.get('/api/events/{event_id}/reviews')
async def reviews(event_id:str): return clean(await db.reviews.find({'event':oid(event_id),'reported':{'$ne':True}}).sort('createdAt',-1).to_list(None))
@app.post('/api/events/{event_id}/reviews',status_code=201)
async def review(event_id:str,body:ReviewIn,user=Depends(current)):
    attended=await db.bookings.find_one({'user':user['_id'],'event':oid(event_id),'checkedIn':True,'status':'confirmed'})
    if not attended: raise HTTPException(403,'Only verified attendees can review this event')
    await db.reviews.update_one({'event':oid(event_id),'user':user['_id']},{'$set':{'rating':body.rating,'comment':body.comment,'reported':False,'createdAt':datetime.now(timezone.utc)}},upsert=True); return {'ok':True}
@app.post('/api/reviews/{review_id}/report')
async def report(review_id:str,_=Depends(current)): await db.reviews.update_one({'_id':oid(review_id)},{'$set':{'reported':True}}); return {'message':'Review reported'}

@app.get('/api/waitlist')
async def waitlist(user=Depends(current)): return clean(await db.waitlists.find({'user':user['_id']}).sort('createdAt',-1).to_list(None))
@app.post('/api/waitlist/{event_id}',status_code=201)
async def join_waitlist(event_id:str,user=Depends(current)):
    if await db.waitlists.find_one({'event':oid(event_id),'user':user['_id']}): raise HTTPException(409,'You are already on this waitlist')
    row={'event':oid(event_id),'user':user['_id'],'createdAt':datetime.now(timezone.utc)}; row['_id']=(await db.waitlists.insert_one(row)).inserted_id; return clean(row)
@app.post('/api/coupons/validate')
async def coupon(body:CouponIn,user=Depends(current)):
    coupon=await db.coupons.find_one({'code':body.code.upper(),'isActive':True})
    if not coupon or body.amount<coupon.get('minimumAmount',0): raise HTTPException(400,'Coupon is not valid for this booking')
    discount=body.amount*coupon['discountValue']/100 if coupon.get('discountType')=='percentage' else coupon['discountValue']; return {'coupon':{'code':coupon['code']},'discount':min(discount,body.amount),'total':max(0,body.amount-discount)}
@app.get('/api/wallet')
async def wallet(user=Depends(current)):
    rows=await db.wallettransactions.find({'user':user['_id']}).sort('createdAt',-1).to_list(None); return clean({'balance':sum(row.get('points',0) for row in rows),'transactions':rows})
@app.post('/api/assistant')
async def assistant(body:MessageIn,user=Depends(current)): return {'answer':'Assistant provider configuration will be migrated separately; your message was received.'}
