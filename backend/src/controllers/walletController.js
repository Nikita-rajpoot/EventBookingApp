import {WalletTransaction} from '../models/index.js';
export async function walletHistory(req,res){const transactions=await WalletTransaction.find({user:req.user.id}).sort({createdAt:-1});res.json({balance:transactions.reduce((total,item)=>total+item.points,0),transactions})}
