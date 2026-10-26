import {MaterialCommunityIcons} from '@expo/vector-icons';
import {StyleSheet,View} from 'react-native';
import {Text} from 'react-native-paper';

type Props={light?:boolean;compact?:boolean};

export function BrandLogo({light=false,compact=false}:Props){
  const color=light?'#FFFFFF':'#27104F';
  return <View style={[s.wrap,compact&&s.compact]}><View style={[s.mark,compact&&s.smallMark]}><MaterialCommunityIcons name="star-four-points" size={compact?17:22} color="#FFFFFF" /></View><Text style={[s.word,{color},compact&&s.smallWord]}>TaeVerse</Text></View>
}
const s=StyleSheet.create({wrap:{flexDirection:'row',alignItems:'center',gap:10},compact:{gap:7},mark:{width:38,height:38,borderRadius:14,backgroundColor:'#A855F7',alignItems:'center',justifyContent:'center',transform:[{rotate:'-10deg'}],shadowColor:'#4C1D95',shadowOpacity:.28,shadowRadius:8,elevation:5},smallMark:{width:28,height:28,borderRadius:10},word:{fontSize:30,fontWeight:'900',letterSpacing:-1.3},smallWord:{fontSize:20,letterSpacing:-.7}});
