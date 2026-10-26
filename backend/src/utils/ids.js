import {v4 as uuid} from 'uuid';export const bookingId=()=>`EV-${uuid().slice(0,8).toUpperCase()}`;export const ticketId=()=>`TK-${uuid().slice(0,8).toUpperCase()}`;
