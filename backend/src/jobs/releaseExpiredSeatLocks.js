import {SeatLock} from '../models/index.js';export async function releaseExpiredSeatLocks(){return SeatLock.deleteMany({expiresAt:{$lte:new Date()}})}
