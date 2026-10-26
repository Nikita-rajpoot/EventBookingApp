export type Category = 'Music'|'Business'|'Food'|'Arts'|'Sports'|'Technology'|'Wellness'|'Comedy'|'Nightlife'|'Workshops';
export type SeatCategory='Regular'|'Premium'|'VIP';
export type SeatStatus='available'|'selected'|'locked'|'booked'|'disabled';
export interface Seat {id:string;label:string;category:SeatCategory;status:Exclude<SeatStatus,'selected'>;price:number}
export interface Event { _id:string; title:string; category:Category; date:string; time:string; location:string; price:number; image:string; gallery?:string[]; description:string; organizer:string; seats:number; ticketTypes:{name:string; price:number; remaining:number}[]; seatLayout?:Seat[]; featured?:boolean; externalUrl?:string; source?:string }
export interface Booking { _id:string; bookingId:string; event:Event; ticketType:string; quantity:number; total:number; status:'confirmed'|'cancelled'; ticketStatus?:'ACTIVE'|'USED'|'CANCELLED'|'EXPIRED'; seatNumbers?:string[]; attendeeNames?:string[]; createdAt:string; userName:string }
export interface User { id:string; name:string; email:string; role:'user'|'organizer'|'admin'; avatar?:string }
