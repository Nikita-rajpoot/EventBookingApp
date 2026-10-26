import { MD3LightTheme } from 'react-native-paper';
export const colors = { primary:'#7C3AED', primaryDeep:'#4C1D95', primarySoft:'#F3E8FF', accent:'#C084FC', ink:'#201333', muted:'#766B84', surface:'#FFFFFF', canvas:'#FBF9FF', success:'#18A66A', danger:'#DD405A', gold:'#F5A623' };
export const theme = { ...MD3LightTheme, colors:{...MD3LightTheme.colors, primary:colors.primary, secondary:colors.accent, background:colors.canvas, surface:colors.surface, onSurface:colors.ink, outline:'#E9DDF7'} };
