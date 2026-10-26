import {ReactNode} from 'react';import {PaperProvider} from 'react-native-paper';import {AppProvider} from '@/context/AppContext';import {theme} from '@/constants/theme';
export function AppProviders({children}:{children:ReactNode}){return <PaperProvider theme={theme}><AppProvider>{children}</AppProvider></PaperProvider>}
