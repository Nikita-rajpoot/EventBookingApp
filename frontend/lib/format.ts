export const formatCurrency=(amount:number)=>`₹${amount.toLocaleString('en-IN')}`;export const formatEventDate=(date:string)=>new Date(date).toLocaleDateString('en-IN',{day:'numeric',month:'short'});
