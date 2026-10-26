export const env={port:Number(process.env.PORT||4000),clientOrigin:process.env.CLIENT_ORIGIN?.split(',')||true,seatLockMinutes:Number(process.env.SEAT_LOCK_MINUTES||10)};
