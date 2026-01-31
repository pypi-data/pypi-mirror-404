from typing import Any, Dict, List, Tuple, Optional
from FFSeval import FFS as ffs
# ご提示のデータ構造
class Parse:
    def __init__(self):
        self.cls = ffs.Treat()
        self.df: Dict[str, Any] = {
        'J':{
                '平板':{
                    '半楕円表面亀裂':[
                        ['J-1-a','三浦らの解',['a','c','P','M']]],
                    '長い表面亀裂(片側)':[
                        ['J-1-b','Kumarらの解',['t','a','c','P','L']]
                    ],
                    '貫通亀裂':[
                        ['J-1-d','Kumarらの解',['P','t','c','a','b']]
                    ],
                    '楕円内部亀裂':[
                        ['J-1-e','半楕円表面亀裂へのモデル化',['t','a','c','b','P']]
                    ]
                },
                '円筒':{
                    '軸方向内表面半楕円表面亀裂':[
                        ['J-2-a','Zahoorの解',['Ri','Ro','R','a','c','P']]
                    ],
                    '軸方向内表面長い表面亀裂':[
                        ['J-2-b','Zahoorの解',['Ri','Ro','R','a','P']]
                    ],
                    '軸方向貫通亀裂':[
                        ['J-2-e','Zahoorの解',['R','t','c','p']]
                    ],
                    '周方向内表面半楕円表面亀裂':[
                        ['J-2-f','Zahoorの解',['Ri','Ro','R','a','c','P']]
                    ],
                    '周方向内表面扇形表面亀裂':[
                        ['J-2-g-a','Zahoorの解',['Ri','Ro','R','a','theta','P']]
                    ],
                    '周方向内表面扇形表面亀裂':[
                        ['J-2-g-b','Zahoorの解',['Ri','Ro','R','a','theta','M']]
                    ],
                    '周方向内表面全周亀裂':[
                        ['J-2-h','Zahoorの解',['Ri','Ro','R','a','P']]
                    ],
                    '周方向貫通亀裂':[
                        ['J-2-k-a','Zahoorの解',['R','t','theta','M','P','n','E','Nu','Sy','Su','S0','Case','e0','alpha','plane','JR','J1c'],[53.,9.,28./53.,0.0,0.0,7.0,192.08e3,0.3,313.6,490.0,313.6,'Collapse',313.6/192.08e3,5.5,'strain',1.76*0.25e-3*0.44,0.784e3],"#"+str({'P0': 629381.6368989643, 'M0': 22619907.48881313})],
                        ['J-2-k-b','Zahoorの解',['R','t','theta','P','M']]
                    ],
                    '周方向内表面貫通と表面の複合亀裂':[
                        ['J-2-m','Zahoorの解',['R','t','a','theta','M']]
                    ]
                },
                '円孔縁':{
                    '片側貫通亀裂':[
                        ['J-7-a','Zahoorの解',['R','a','alpha','sigma','sigma0','lambda'],]
                    ]
                },
            },
            'K': {
                '平板': {
                    '半楕円表面亀裂': [
                        ['K-1-a-1', 'Raju-Newmanの解',['a','c','b','t','P','M'],[10.,30.,100.,40.,3.8e7,5.0e5],"#"+str({'KA': 28383.37159904204, 'KB': 18391.925464059223})],
                        ['K-1-a-2', 'ASME Section XI,Appendix Aの解',['a','c','t','Sy','sigma0','sigma1','sigma2','sigma3'],[10e-3,30e-3,40e-3,380.,50.0,-42.143,-3.571,15.714],"#"+str({'KA': 5.226514393344583, 'KB': 5.128123890300543})],
                        ['K-1-a-3', '白鳥の解',['a','c','t',
                        'Sy',
                        'sigma0','sigma1','sigma2','sigma3','t'],[10e-3,30e-3,40e-3,380.,50.,-42.143,-3.571,15.714],"#"+str({'KA': 6.466855504266251, 'KB': 2.6883628116803386})],
                    ],
                    '長い表面亀裂': [
                        ['K-1-b-1','Tadaらの解(片側)',['a','c','b','t','P','M'],[10.,30.,100.,40.,3.8e7,5.0e5],"#"+str({'K': 39834.07041328842})],
                        ['K-1-b-2','Wu-Carlssonの解(片側)',['b','t','a','sigma0','sigma1','sigma2','sigma3']],
                        ['K-1-c-1','Tadaらの解(両側)',['t','a','b','P'],[16.0,4.0,100.,1000.],"#"+str({'K': 1.2881249999999997})],
                        ['K-1-c-2','Wu-Carlssonの解(両側)',['b','t','a','sigma0','sigma1','sigma2','sigma3']],
                    ],
                    '中央貫通亀裂': [
                        ['K-1-d-1','Shihらの解(亀裂が短い場合)',['t','c','b','P','M'],[16.,4.0,100.,1000.,2000.],"#"+str({'KA': 1.938621399427908, 'KB': 0.27694591420398684})],
                        ['K-1-d-2','Tadaらの解(亀裂が長い場合)',['t','c','b','P'],[16.,4.,100.,1000.],"#"+str({'K': 1.1088340712310085})],
                    ],
                    '楕円内部亀裂':[
                        ['K-1-e-1','Ovchinnikov-Vasiltchenkoの解',['a','c','b','t','e','P','M'],[10.,30.,100.,40.,5.,3.8e7,5.0e5],"#"+str({'KA': 31426.61218537177, 'KB': 31470.035300651736})],
                        ['K-1-e-2','ASME Section XI,Appendix Aの解',['a','c','e','b','t','P','M','Sy'],[5.,10.,3.,100.,40.,3.8e2,1.e2,480.],"#"+str({'KA': 0.16001875849927416, 'KB': 0.1571181809043095})],
                        ['K-1-e-3','Raju-Newmanの解',['a','c','b','t','P'],[10.,30.,100.,40.,3.8e7],"#"+str({'KA': 24572.130377539143, 'KC': 14162.975988557064})]
                    ],
                },
                '円筒':{
                    '軸方向内表面半楕円表面亀裂':[
                        ['K-2-a-1','Fettらの解',['Ri','t','a','c','sigma0','sigma1','sigma2','sigma3'],[275.,16.,0.8,2.4,10.,0.,0.,0.],"#"+str({'KA': 8.345699382302255, 'KB': 6.610985918151353})],
                        ['K-2-a-2','白鳥の解(長い表面亀裂)',['Ri','t','a','c','sigma0','sigma1','sigma2','sigma3'],[275.,16.,0.8,2.4,10.,0.,0.,0.],"#"+str({'KA': 12.273214856554826, 'KB': 9.751971290065198})],
                        ['K-2-a-3','Zahoorの解',['Ro','Ri','t','p','a','c'],[291.,275.,16.,8.,0.8,2.4],"#"+str({'KA': 294.83824754772655, 'KB': 199.32266060603146})]
                    ],
                    '軸方向内表面長い表面亀裂':[
                        ['K-2-b-1','Fuhley-Osageの解',['Ri','t','a','sigma0','sigma1','sigma2','sigma3','sigma4'],[275.,16.,0.8,10.,0.,0.,0.,0.],"#"+str({'K': 0.13385934283098297})],
                        ['K-2-b-2','Zahoorの解',['Ri','Ro','t','a','p'],[275.,291.,16.,0.8,8.],"#"+str({'K': 264.57512533028677})]
                    ],
                    '軸方向外表面半楕円表面亀裂':[
                        ['K-2-c-1','Fettらの解',['Ri','t','a','c','sigma0','sigma1','sigma2','sigma3'],[275.,16.,0.8,0.8,10.0,0.,0.,0.,0.],"#"+str({'KA': 4.321169717297702, 'KB': 7.756717367175594})],
                        ['K-2-c-2','Zahoorの解',['Ro','Ri','t','p','a','c'],[291.,275.,16.,8.,0.8,0.8],"#"+str({'KA': 256.0595310744639, 'KB': 256.2707801876004})]               
                    ],
                    '軸方向外表面長い表面亀裂':[
                        ['K-2-d','Fuhley-Osageの解',['Ri','t','a','sigma0','sigma1','sigma2','sigma3','sigma4'],[275.,16.,0.8,10.,0.,0.,0.,0.],"#"+str({'K': 2.960983117555932})]
                    ],
                    '軸方向貫通亀裂':[
                        ['K-2-e-1','Erdogan-Kiblerの解',['Ri','t','c','sigma_m','sigma_b'],[275.,16.,0.8,10.,2.],"#"+str({'KA': 19.33925802994556, 'KB': 13.492199128158157})],
                        ['K-2-e-2','ASME Code Case N-513の解',['R','t','c','p'],[283.,16.,8.,0.8,5.0],"#"+str({'K': 72.17166404566943})],
                        ['K-2-e-3','Zangの解',['Ro','Ri','t','c','sigma0','sigma1','sigma2','sigma3','sigma4']]
                    ],
                    '周方向内表面半楕円表面亀裂':[
                        ['K-2-f-1','Chapuliotらの解',['Ri','t','c','a','sigma0','sigma1','sigma2','sigma3','sigma_bg'],[275.,16.,0.8,0.2,10.,0.,0.,0.,2.],"#"+str({'KA': 1.0313674563838071, 'KB': 4.553395052778607})],
                        ['K-2-f-2','白鳥の解',['Ri','t','c','a','sigma_m','sigma_bg'],[275.,16.,0.8,0.2,10.,2.],"#"+str({'KA': 8.46116856227208, 'KB': 3.8017840690864952})],
                        ['K-2-f-3','Zahoorの解',['Ri','t','c','a','P','M'],[275.,16.,0.8,0.2,100000.,2000.],"#"+str({'K': 2.8266286559160996})]
                    ],
                    '周方向内表面扇形表面亀裂':[
                        ['K-2-g','ASME Section XI,Appendix Cの解',['R','Ri','t','c','a','P','M'],[293.,275.,16.,0.8,0.2,3.8e2,1e2],"#"+str({'KA': 0.011288380164694913})]
                    ],
                    '周方向内表面全周亀裂':[
                        ['K-2-h-1','Fuhley-Osageの解',['Ri','t','a','sigma0','sigma1','sigma2','sigma3','sigma4']],
                        ['K-2-h-2','飯井らの解',['R','t','a','M','H']]
                    ],
                    '周方向外表面半楕円表面亀裂':[
                        ['K-2-i-1','Chpuliotらの解',['Ri','a','t','c','sigma0','sigma1','sigma2','sigma3','sigma_bg']],
                        ['K-2-i-2','白鳥の解',['R','a','t','c','sigma_m','sigma_bg']]
                    ],
                    '周方向外表面全周亀裂':[
                        ['K-2-j','Fuhley-Osageの解',['Ri','t','a','sigma0','sigma1','sigma2','sigma3','sigma4']]
                    ],
                    '周方向貫通亀裂':[
                        ['K-2-k-1','Sattari-Farの解',['Ri','t','c','sigma_m','sigma_b','sigma_bg']],
                        ['K-2-k-2','ASME Code Case N-513の解',['R','t','c','P','M'],[293.,16.,0.8,3.8e2,1.e2],"#"+str({'K': 0.020495409430623644})],
                        ['K-2-k-3','Zahoorの解',['R','t','c','P','M']],
                        ['K-2-k-4','Zangの解',['Ri','t','c','sigma0','sigma1','sigma2','sigma3','sigma4','sigma_bg']],
                    ],
                    '軸方向内表面一定深さ矩形表面亀裂':[
                        ['K-2-l','ASME Section XI, Appendix Cの解',['R','t','a','c','p']]
                    ],
                },
                'ノズル':{
                    'コーナー部の軸方向内表面半楕円表面亀裂':[
                        ['K-3-a','白鳥の解',['Ris','Rm','ts','tm','ro','ri','sigma_m']],
                    ],
                    'コーナー部の軸方向内表面1/4表面亀裂':[
                        ['K-3-b-1','Kobayashiらの解',['Ris','Rm','ts','tm','ro','ri','sigma_00','sigma_10','sigma_01','sigma_20','sigma_02','sigma_30','sigma03']],
                        ['K-3-b-2','Fifeらの解',['Ris','Rm','ts','tm','a','c','sigma0','sigma1','sigma2','sigma3']]
                    ],
                    '周方向内表面全周表面亀裂':[
                        ['K-3-c-1','Buchlet-Bamfordの解(配管継目付近にある亀裂)',['R','t','a','sigma0','sigma1','sigma2','sigma3']],
                        ['K-3-c-2','Buchlet-Bamfordの解(ノズル補強部にある亀裂)',['R','t','a','sigma0','sigma1','sigma2','sigma3']],
                        ['K-3-c-3','Buchlet-Bamfordの解(ノズルコーナー部にある亀裂)',['R','t','a','sigma0','sigma1','sigma2','sigma3']],
                    ]
                },
                '配管エルボ':{
                    '横腹の軸方向内表面半楕円表面亀裂':[
                        ['K-4-a-1','Viswnalhaらの解',['Do','R','a','c','t','p','M']],
                        ['K-4-a-2','Mohanらの解',['Dm','R','a','c','t','p','M']]
                    ],
                    '横腹の軸方向貫通亀裂':[
                        ['K-4-b-1','Kozlukらの解',['Do','R','c','t','p','M']],
                        ['K-4-b-2','Chattopadhyayらの解',['Dm','R','c','t','p']]
                    ],
                    '背側の軸方向貫通亀裂':[
                        ['K-4-c','Gebner-Hoflerの解',['Do','R','c','t','p']]
                    ],
                    '背側の周方向内表面半楕円表面亀裂':[
                        ['K-4-d','Mohanらの解',['Do','R','a','c','t','p','M']]
                    ],
                    '背側の周方向貫通亀裂':[
                        ['K-4-e','Chattopadhyayらの解',['Dm','R','c','t','p','M']]
                    ]
                },
                '配管ティー':{
                    '軸方向貫通亀裂':[
                        ['K-5-a','Linらの解',['Rm','rm','t','T','c','p']]
                    ],
                    '周方向外表面半楕円表面亀裂':[
                        ['K-5-b-1','Du-Hancockの解',['Ro','ro','T','t','c','P']],
                        ['K-5-b-2','Bowness-Leeの解',['Ro','ro','T','t','c','a','H','P']],
                        ['K-5-b-3','Olowokere-Nwosuの解',['Ro','ro','T','t','c','a','H','P','Mi','Mo']]
                    ]
                },
                '球殻':{
                    '内表面全周亀裂':[
                        ['K-6-a','Fuhrey-Osageの解',['Ri','t','a','sigma0','sigma1','sigma2','sigma3','sigma4']]
                    ],
                    '外表面全周亀裂':[
                        ['K-6-b','FhreyOsageの解',['Ro','t','a','sigma0','sigma1','sigma2','sigma3','sigma4']]
                    ],
                    '貫通亀裂':[
                        ['K-6-c','Erdogan-Kiblerの解',['R','t','c','sigma_m','sigma_b']]
                    ]
                },
                '円孔縁':{
                    '両側1/4楕円コーナー亀裂':[
                        ['K-7-a','Raju-Newmanの解',['a','c','t','b','r','P','M']]
                    ],
                    '片側1/4楕円コーナー亀裂':[
                        ['K-7-b','Raju-Newmanの解',['a','c','t','b','r','P','M']]
                    ],
                    '両側貫通亀裂':[
                        ['K-7-c','Rooke-Cartwrightの解',['b','r','c','sigma_m','sigma_b']]
                    ],
                    '片側貫通亀裂':[
                        ['K-7-d','Rooke-Cartwrightの解',['b','r','c','sigma_m','sigma_b']]
                    ],
                    '両側内部半楕円亀裂':[
                        ['K-7-e','Raju-Newmanの解',['a','c','t','b','r','P','M']]
                    ],
                    '片側内部半楕円亀裂':[
                        ['K-7-f','Raju-Newmanの解',['b','r','c','a','P']]
                    ],       
                },
                '丸棒':{
                    '周方向全周表面亀裂':[
                        ['K-8-a','Tadaらの解',['Ro','a','P','M']]
                    ],
                    '周方向直線前縁表面亀裂':[
                        ['K-8-b','Sihの解',['Ro','a','P','M']]
                    ],
                    '周方向半円表面亀裂':[
                        ['K-8-c','APIの解',['Ro','a','P','M']]
                    ]
                },
                'ボルト':{
                    '周方向直線前縁表面亀裂':[
                        ['K-8-d','James-Millsの解',['Rth','a','P','M']]
                    ]                    
                }

            },
            'L': {
                '平板':{
                    '半楕円表面亀裂':[
                        ['L-1-a','Dirstrom & Sattari-Farの解',['w','t','a','P','M','Sy']]
                    ],
                    '長い表面亀裂':[
                        ['L-1-b','片側',['w','t','a','P','M','Sy']],
                        ['L-1-c','両側',['w','t','a','P','Sy']]
                    ],
                    '貫通亀裂':[
                        ['L-1-d','Milneの解',['w','t','l','P','M','Sy']]
                    ],
                    '楕円内部亀裂':[
                        ['L-1-e','Willoughbyの解',['w','t','l','a','P','M','Sy']]
                    ]
                },
                '円筒':{
                    '軸方向内表面亀裂':[
                        ['L-2-a','半楕円表面亀裂',['Ri','Rm','t','a','l','sigma_m','Sy']],
                        ['L-2-b','長い表面亀裂',['Ri','t','a','p','Sy']]
                    ],
                    '軸方向外表面亀裂':[
                        ['L-2-c','半楕円表面亀裂',['Ri','Rm','t','a','l','sigma_m','Sy']],
                        ['L-2-d','長い表面亀裂',['Ro', 't','a','l','sigma_m','Sy']]
                    ],
                    '軸方向貫通亀裂':[
                        ['L-2-e','Kiefnerの解',['Ri','Rm','t','l','p','Sy']]
                    ],
                    '周方向内表面亀裂':[
                        ['L-2-f','半楕円表面亀裂',['Ri','Rm','Ro','theta','a','P','M','Sy']],
                        ['L-2-h','全周表面亀裂',['Ri','t','a','P','M','Sy']]
                    ],
                    '周方向外表面亀裂':[
                        ['L-2-i','半楕円表面亀裂',['Ri','t','a','P','M','sigma_m','sigma_mg','Sy']],
                        ['L-2-j','全周表面亀裂',['Ri','t','a','P','M','sigma_m','sigma_mg','Sy']]
                    ],
                    '周方向貫通亀裂':[
                        ['L-2-k-1','軸力の解',['Ri','Rm','Ro','t','theta','P','Sy']],
                        ['L-2-k-2','曲げモーメントの解',['Ri','Rm','Ro','t','theta','M','Sy']],
                        ['L-2-k-3','軸力と曲げモーメントの解',['Ri','Rm','Ro','t','theta','P','M','Sy']],
                        ['L-2-k-4','膜応力と管曲げ応力の解',['Ri','Rm','Ro','t','theta','sigma_m','sigma_mg','Sy']]
                    ],
                    '軸方向内表面1/4円コーナ表面亀裂':[
                        ['L-3-b','',['Ris','Rim','ts','tm','tn','a','p','Sy']]
                    ]
                },
                '球殻':{
                    '貫通亀裂':[
                        ['L-6-c','Berdekin, Taylorの解',['Ri','t','l','sigma_m','sigma_b','Sy']],
                    ]
                },
                '円孔縁':{
                    '片側1/4楕円コーナー亀裂':[
                        ['L-7-b','ASTMの解',['w','t','R','l','sigma_m','sigma_bg','Sy']]
                    ]
                }
            }
           
        }
        #日本語同義語/正規化用（必要に応じて追加）
        self.ALIASES = {
                'コーナー部の軸方向内表面半楕円表面亀裂':['コーナー部の軸方向内表面半楕円表面亀裂'],
                '周方向直線前縁表面亀裂':['周方向直線前縁表面亀裂'],
                '応力拡大係数': ['応力拡大係数', 'K値', 'K 係数', 'K'],
                'J積分': ['J積分', 'J値', 'J積分係数','J'],
                '平板': ['平板', 'プレート', '板','帯板'],
                '円筒':['円筒','pipe','配管','菅'],
                '丸棒':['丸棒'],
                '配管エルボ':['配管エルボ','elbow'],
                '配管ティー':['配管ティー'],
                'ノズル':['ノズル','nozzle'],
                '球殻':['球殻'],
                '円孔縁':['円孔縁'],
                'ボルト':['ボルト'],
                '周方向半円表面亀裂':['周方向半円表面亀裂'],
                '両側1/4楕円コーナー亀裂':['両側1/4楕円コーナー亀裂'],
                '片側1/4楕円コーナー亀裂':['片側1/4楕円コーナー亀裂'],
                'コーナー部の軸方向内表面1/4表面亀裂':['コーナー部の軸方向内表面1/4表面亀裂'],
                '周方向全周表面亀裂':['周方向全周表面亀裂'],
                '周方向内表面全周表面亀裂':['周方向内表面全周表面亀裂'],
                '周方向内表面全周亀裂':['周方向内表面全周亀裂'],
                '軸方向内表面半楕円表面亀裂':['軸方向内表面半楕円表面亀裂'],
                '軸方向内表面長い表面亀裂':['軸方向内表面長い表面亀裂'],
                '軸方向内表面1/4円コーナ表面亀裂':['軸方向内表面1/4円コーナ表面亀裂'],
                '長い表面亀裂(片側)':['長い表面亀裂(片側)'],
                '軸方向外表面半楕円表面亀裂':['軸方向外表面半楕円表面亀裂'],
                '軸方向外表面長い表面亀裂':['軸方向外表面長い表面亀裂'],
                '軸方向貫通亀裂':['軸方向貫通亀裂'],
                '背側の軸方向貫通亀裂':['背側の軸方向貫通亀裂'],
                '横腹の軸方向貫通亀裂':['横腹の軸方向貫通亀裂'],
                '横腹の軸方向内表面半楕円表面亀裂':['横腹の軸方向内表面半楕円表面亀裂'],
                '軸方向内表面一定深さ矩形表面亀裂':['軸方向内表面一定深さ矩形表面亀裂'],
                '周方向内表面半楕円表面亀裂':['周方向内表面半楕円表面亀裂'],
                '背側の周方向内表面半楕円表面亀裂':['背側の周方向内表面半楕円表面亀裂'],
                '周方向外表面半楕円表面亀裂':['周方向外表面半楕円表面亀裂'],
                '周方向内表面扇形表面亀裂':['周方向内表面扇形表面亀裂'],
                '周方向内表面亀裂':['周方向内表面亀裂'],
                '周方向外表面亀裂':['周方向外表面亀裂'],
                '周方向貫通亀裂':['周方向貫通亀裂'],
                '周方向直線前縁表面亀裂':['周方向直線前縁表面亀裂'],
                '内表面全周亀裂':['内表面全周亀裂'],
                '外表面全周亀裂':['外表面全周亀裂'],
                '背側の周方向貫通亀裂':['背側の周方向貫通亀裂'],
                '軸方向内表面亀裂':['軸方向内表面亀裂'],
                '軸方向外表面亀裂':['軸方向外表面亀裂'],
                '周方向内表面貫通と表面の複合亀裂':['周方向内表面貫通と表面の複合亀裂'],
                '半楕円表面亀裂': ['半楕円表面亀裂', '半だえん表面き裂', '半楕円き裂', '表面半楕円亀裂'],
                '楕円内部亀裂':['楕円内部亀裂','だえん内部亀裂'],
                '長い表面亀裂': ['長い表面亀裂', 'ロング表面亀裂', '長尺表面亀裂'],
                '中央貫通亀裂': ['中央貫通亀裂', 'センター貫通亀裂', '中心貫通亀裂'],

                '崩壊荷重': ['崩壊荷重', 'L'],
                '両側1/4楕円コーナー亀裂':['両側1/4楕円コーナー亀裂'],
                '貫通亀裂':['貫通亀裂'],
                '両側貫通亀裂':['両側貫通亀裂'],
                '片側貫通亀裂':['片側貫通亀裂'],
                '両側内部半楕円亀裂':['両側内部半楕円亀裂'],
                '片側内部半楕円亀裂':['片側内部半楕円亀裂'],
}
    def find_entry(self, code: str
               ) -> Optional[Tuple[str, str, str, List[Any]]]:
        """
        与えられた辞書 df から、コード（例: 'J-1-a'）に一致するエントリを探し、
        見つかった場合は (カテゴリ, 形状, 亀裂タイプ, エントリ全体) を返します。
        
        返却例:
        ('J', '平板', '半楕円表面亀裂', ['J-1-a', '三浦らの解', ['a','c','P','M']])

        見つからない場合は None を返します。
        """
        # トップレベル: 'J', 'K', 'L'
        for category, shapes in self.df.items():
            # 形状レベル: '平板', '円筒', '円孔縁', ...
            for shape, crack_types in shapes.items():
                # 亀裂タイプレベル: '半楕円表面亀裂', '長い表面亀裂(片側)', ...
                for crack_type, entries in crack_types.items():
                    # entries はリスト。各要素が ['コード', '解の出典', [パラメータ...], ...] の形
                    for entry in entries:
                        if isinstance(entry, list) and entry:
                            if entry[0] == code:
                                return (category, shape, crack_type, entry)
        return None
    def match_alias(self, text: str, candidates: List[str]) -> bool:
        """text が candidates のいずれかを含むかを判定（部分一致）"""
        t = text.strip()
        return any(alias in t for alias in candidates)
    def parse_query(self,query: str) -> Optional[Tuple[str, List[str]]]:
        """
        日本語の問い合わせ文から、
        - ルートキー（'K' / 'J' / 'L' 等）
        - 階層パス（例：['平板', '半楕円表面亀裂']）
        を抽出する。
        """
        q = query.strip()

        # ルートキーの推定（ここでは K にフォーカス）
        root_key = None
        if self.match_alias(q, self.ALIASES['応力拡大係数']) or "K" in q:
            root_key = 'K'
        elif any(word in q for word in ['J積分', 'J積分値', 'J値']):
            root_key = 'J'
        elif any(word in q for word in ['L','崩壊荷重']):
            root_key = 'L'

        if root_key is None:
            return None

        # 階層（K の中身に対する候補）
        path: List[str] = []
        # 第一階層候補（例：平板などの構造カテゴリ）
        if self.match_alias(q, self.ALIASES['平板']):
            path.append('平板')
        if self.match_alias(q, self.ALIASES['円筒']):
            path.append('円筒')
        if self.match_alias(q, self.ALIASES['ノズル']):
            path.append('ノズル')
        if self.match_alias(q, self.ALIASES['配管エルボ']):
            path.append('配管エルボ')
        if self.match_alias(q, self.ALIASES['配管ティー']):
            path.append('配管ティー')
        if self.match_alias(q, self.ALIASES['球殻']):
            path.append('球殻')
        if self.match_alias(q, self.ALIASES['円孔縁']):
            path.append('円孔縁')
        if self.match_alias(q, self.ALIASES['丸棒']):
            path.append('丸棒')
        if self.match_alias(q, self.ALIASES['ボルト']):
            path.append('ボルト')
        # 第二階層候補（亀裂形状）
        if self.match_alias(q, self.ALIASES['コーナー部の軸方向内表面半楕円表面亀裂']):
            path.append('コーナー部の軸方向内表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['コーナー部の軸方向内表面1/4表面亀裂']):
            path.append('コーナー部の軸方向内表面1/4表面亀裂')
        elif self.match_alias(q, self.ALIASES['横腹の軸方向内表面半楕円表面亀裂']):
            path.append('横腹の軸方向内表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['両側1/4楕円コーナー亀裂']):
            path.append('両側1/4楕円コーナー亀裂')
        elif self.match_alias(q, self.ALIASES['片側1/4楕円コーナー亀裂']):
            path.append('片側1/4楕円コーナー亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向内表面1/4円コーナ表面亀裂']):
            path.append('軸方向内表面1/4円コーナ表面亀裂')            
            
        elif self.match_alias(q, self.ALIASES['横腹の軸方向貫通亀裂']):
            path.append('横腹の軸方向貫通亀裂')
        elif self.match_alias(q, self.ALIASES['背側の軸方向貫通亀裂']):
            path.append('背側の軸方向貫通亀裂')
        elif self.match_alias(q, self.ALIASES['背側の周方向内表面半楕円表面亀裂']):
            path.append('背側の周方向内表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['背側の周方向貫通亀裂']):
            path.append('背側の周方向貫通亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面全周表面亀裂']):
            path.append('周方向内表面全周表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向内表面亀裂']):
            path.append('軸方向内表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向外表面亀裂']):
            path.append('軸方向外表面亀裂')

        elif self.match_alias(q, self.ALIASES['外表面全周亀裂']):
            path.append('外表面全周亀裂')
        elif self.match_alias(q, self.ALIASES['周方向全周表面亀裂']):
            path.append('周方向全周表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向直線前縁表面亀裂']):
            path.append('周方向直線前縁表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向半円表面亀裂']):
            path.append('周方向半円表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面貫通と表面の複合亀裂']):
            path.append('周方向内表面貫通と表面の複合亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面亀裂']):
            path.append('周方向内表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向外表面亀裂']):
            path.append('周方向外表面亀裂')

        elif self.match_alias(q, self.ALIASES['軸方向内表面半楕円表面亀裂']):
            path.append('軸方向内表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向内表面長い表面亀裂']):
            path.append('軸方向内表面長い表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向外表面半楕円表面亀裂']):
            path.append('軸方向外表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向外表面長い表面亀裂']):
            path.append('軸方向外表面長い表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向内表面一定深さ矩形表面亀裂']):
            path.append('軸方向内表面一定深さ矩形表面亀裂')
        elif self.match_alias(q, self.ALIASES['軸方向貫通亀裂']):
            path.append('軸方向貫通亀裂')
        elif self.match_alias(q, self.ALIASES['周方向貫通亀裂']):
            path.append('周方向貫通亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面扇形表面亀裂']):
            path.append('周方向内表面扇形表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面半楕円表面亀裂']):
            path.append('周方向内表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向外表面半楕円表面亀裂']):
            path.append('周方向外表面半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['半楕円表面亀裂']):
            path.append('半楕円表面亀裂')
        elif self.match_alias(q, self.ALIASES['周方向内表面全周亀裂']):
            path.append('周方向内表面全周亀裂')
        elif self.match_alias(q, self.ALIASES['内表面全周亀裂']):
            path.append('内表面全周亀裂')
            
        elif self.match_alias(q, self.ALIASES['中央貫通亀裂']):
            path.append('中央貫通亀裂')
        elif self.match_alias(q, self.ALIASES['楕円内部亀裂']):
            path.append('楕円内部亀裂')

        elif self.match_alias(q, self.ALIASES['両側貫通亀裂']):
            path.append('両側貫通亀裂')
        elif self.match_alias(q, self.ALIASES['片側貫通亀裂']):
            path.append('片側貫通亀裂')
        elif self.match_alias(q, self.ALIASES['周方向直線前縁表面亀裂']):
            path.append('周方向直線前縁表面亀裂')
        elif self.match_alias(q, self.ALIASES['長い表面亀裂(片側)']):
            path.append('長い表面亀裂(片側)')
        elif self.match_alias(q, self.ALIASES['長い表面亀裂']):
            path.append('長い表面亀裂')
        elif self.match_alias(q, self.ALIASES['両側内部半楕円亀裂']):
            path.append('両側内部半楕円亀裂')
        elif self.match_alias(q, self.ALIASES['片側内部半楕円亀裂']):
            path.append('片側内部半楕円亀裂')            
        elif self.match_alias(q, self.ALIASES['貫通亀裂']):
            path.append('貫通亀裂')
        return (root_key, path)
    def resolve_path(self, data: Dict[str, Any], root_key: str, path: List[str]) -> Any:
        """
        data（df）から root_key + path で指定されたノードの中身を返す。
        例：root_key='K', path=['平板','半楕円表面亀裂'] → 対応リストを返す。
        """
        node = data.get(root_key, None)
        if node is None:
            raise KeyError(f"データにキー '{root_key}' がありません。")

        for key in path:
            if not isinstance(node, dict):
                raise KeyError(f"パス途中 '{key}' へ辿れません（辞書ではないノードに到達）。")
            if key not in node:
                raise KeyError(f"キー '{key}' が見つかりません。利用可能: {list(node.keys())}")
            node = node[key]
        return node
    def format_output(self,value: Any) -> str:
        """
        ノードの中身（リスト/文字列/辞書）を見やすく文字列化。
        """
        if isinstance(value, list):
            lines = []
            for item in value:
                if isinstance(item, list):
                    # 例：['K_1_a_2', 'ASME Section XI,Appendix Aの解']
                    if len(item) == 2:
                        lines.append(f"- {item[0]}: {item[1]}")
                    else:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"- {item}")
            return "\n".join(lines)
        elif isinstance(value, dict):
            # 辞書ならキー一覧
            keys = ", ".join(list(value.keys()))
            return f"{{{keys}}}"
        else:
            return str(value) 
    def query_df(self,query: str) -> str:
        """
        問い合わせ文を受け取り、該当ノードの内容を文字列で返す。
        """
        parsed = self.parse_query(query)
        if not parsed:
            return "問い合わせから対象キーが特定できませんでした（例：'応力拡大係数', '平板', '半楕円表面亀裂' などを含めてください）。"

        root_key, path = parsed
        try:
            value = self.resolve_path(self.df, root_key, path)
        except KeyError as e:
            return f"パス解決エラー: {e}"

        # 期待動作：応力拡大係数（K）で該当形状の内部データを返す
        header = f"[{root_key}] {' / '.join(path) if path else '(ルート)'}"
        body = self.format_output(value)
        #return f"{header}\n{body}"
        return header, body
    def Search(self,query: str):  
        header, body =self.query_df(query)
        root_key, path=self.parse_query(query)
        value = self.resolve_path(self.df, root_key, path)
        print(f"Category:{header}")
        for d in value:
            if len(d)<=3:
                r='not registered'
            else:
                r='registered'
            print(f"  [{d[0]}]{d[1]}({r})\n    {d[2]}")
        return value
    def GetParam(self,value,key):
        param=sample=answer=None
        for d in value:
            if d[0]==key:
                param=d[2]
                if len(d)==3:
                    print('Not registered yet!')                  
                else:
                    sample=d[3]
                    answer=d[4]
        if param==None:
            print('Not registered!')
        return param,sample,answer
    def MakeDict(self,var_names, var_values):
        '''
        パラメータリストと、値リストから辞書データを作ってもどす
        var_names: パラメータリスト
        var_values: 数値リスト
        '''
        dict_data = dict(zip(var_names, var_values))
        return dict_data
    def SetKey(self,k_id):
        '''
        キーの設定
        k_id: キー
        '''
        self.JKL = self.cls.Set(k_id)
        return
    def Calc(self,dict_data):
        '''
        計算実行
        dict_data: 辞書形式データ
        '''
        self.JKL.SetData(dict_data)
        self.JKL.Calc()
        result=self.JKL.GetRes()
        return result
    def VarOut(self,k_id):
        '''
        キーを与えると、パラメータリスト、数値リスト、正解を戻す
        '''
        category,shape,crack,data=self.find_entry(k_id)
        var_names=data[2]
        var_values=[0.0]*len(var_names)
        answer=None
        if len(data)>3:
            var_values=data[3]
            answer=data[4]
        return var_names,var_values,answer
    def DictOut(self,k_id):
        '''
        キーを与えると、入力データを辞書データとして戻す
        '''
        category,shape,crack,data=self.find_entry(k_id)
        var_names=data[2]
        var_values=[0.0]*len(var_names)
        if len(data)>3:
            var_values=data[3]
        dict_data = dict(zip(var_names, var_values))
        return dict_data
    def Reference(self):
        return self.JKL.GetRefer()
    def __del__(self):
        del self.cls