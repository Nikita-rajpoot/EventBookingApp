import jwt from 'jsonwebtoken';
export function auth(req,res,next){try{req.user=jwt.verify(req.headers.authorization?.split(' ')[1],process.env.JWT_SECRET);next()}catch{res.status(401).json({message:'Authentication required'})}}
export function admin(req,res,next){if(req.user?.role!=='admin')return res.status(403).json({message:'Admin access required'});next()}
export function organizer(req,res,next){if(!['organizer','admin'].includes(req.user?.role))return res.status(403).json({message:'Organizer access required'});next()}
