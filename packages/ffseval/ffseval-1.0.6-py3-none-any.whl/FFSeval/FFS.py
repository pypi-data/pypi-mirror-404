import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
class Base:
    def __init__(self):
        self.title=None
        self.data=None
        self.res=None
        self.refer=None
        self.param=None
    def SetInputItems(self,param:list)->None:
        self.param=param
    def GetInputItems(self)->list:
        return self.param
    def SetTitle(self,title:str)->None:
        self.title=title
    def Title(self)->str:
        return self.title
    def SetData(self,data:dict):
        self.data=data
    def GetData(self):
        return self.data
    def SetRes(self,res:dict):
        self.res=res
    def GetRes(self):
        return self.res
    def SetRefer(self,refer:str):
        self.refer=refer
    def GetRefer(self):
        return self.refer
    def CalcKc(self):
        nu=self.data['Nu']
        E=self.data['E']
        j1c=self.data['J1c']
        Ed=E/(1-nu*nu)
        return np.sqrt(Ed*j1c)
    def Option1(self,Kr,Lr):
        kk=(1-0.14*Lr*Lr)*(0.3+0.7*np.exp(-0.65*Lr**6))
        flag=False
        if Kr<kk:
            flag=True
        return flag,kk
    def DrawOption1(self,Lr0,Kr0,Su,Sy):
        """
        R6法-Rev.3のOption1破壊評価曲線の描画
        Lr0,Kr0描画点
        Su:引張強さ
        Sy:降伏強さ
        """
        compute_Kr = lambda Lr: (1 - 0.14 * Lr**2) * (0.3 + 0.7 * np.exp(-0.65 * Lr**6))
        Sf=(Sy+Su)/2
        Lrmax=Sf/Sy
        Krmax=compute_Kr(Lrmax)
        # Lrの範囲を生成
        Lr_values = np.linspace(0, Lrmax, 500)
        Kr_values = compute_Kr(Lr_values)

        # グラフ描画
        plt.figure(figsize=(8, 5))
        plt.plot(Lr_values, Kr_values,color='blue')
        plt.plot(Lr0, Kr0, 'ro')  # 赤い点をプロット
        plt.plot([Lrmax,Lrmax],[0,Krmax],color='blue')
        plt.ylim(0,1.2)
        plt.xlabel('Lr',fontsize=16)
        plt.ylabel('Kr',fontsize=16)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()        
    def Margin(self,K:float,L:float)->dict:
        '''
        評価点(L,K)について，Option1曲線に対する安全裕度を評価する
        計算する値
        (L0,K0): 原点と評価点の延長線とOption1曲線との交点
        margin: 安全裕度　1以下であれば安全
        '''

        # Krの定義
        Kr1 = lambda Lr: (1 - 0.14 * Lr**2) * (0.3 + 0.7 * np.exp(-0.65 * Lr**6))
        Kr2 = lambda Lr:(K / L) * Lr
        equation=lambda Lr:Kr1(Lr) - Kr2(Lr)
        # 初期値の推測（範囲によって複数回試すと良い）
        initial_guess = 0.5
        solution = fsolve(equation, initial_guess)
        res={}
        res['L0']=solution[0]
        res['K0']=Kr1(solution[0])
        res['margin']=K/res['K0']
        return res
    def RolfeBarsom(self,Cv,Sy)->float:
        #Cv=self.data['Cv']
        #Sy=self.data['Sy']
        cc=np.array(Cv)
        c=0.6478*(cc/Sy-0.0098)
        K1c=np.sqrt(c)*Sy
        return K1c
    def JR(self,C:float,m:float,da:float)->float:
        return C*da**m
class Fatigue:
    '''
    JSME維持規格における炭素鋼および低合金鋼の大気中における疲労亀裂進展特性
    '''
    def __init__(self,cls,data,pfm=False,cov=0.1):
        self.cls=cls
        self.cls.SetData(data)
        self.data=data
        self.pfm=pfm #PFM計算のときTrue
        self.cov=cov #PFM計算のとき，係数Cのcov
    def dadN(self,a,c,Pmin,Pmax):
        self.data['a']=a
        self.data['c']=c
        self.data['P']=Pmin
        self.cls.SetData(self.data)
        self.cls.Calc()
        resMin=self.cls.GetRes()
        self.data['P']=Pmax
        self.cls.SetData(self.data)
        self.cls.Calc()
        resMax=self.cls.GetRes()
        dKA=resMax['KA']-resMin['KA']
        dKB=resMax['KB']-resMin['KB']
        da=self.FatigueSteel(dKA)
        dc=self.FatigueSteel(dKB)
        return da,dc,resMax
    def FatigueSteel(self,dK):
        n=3.07
        da=self.C*dK**n
        return da
    def EvalAC(self,a0,c0,Pmin,Pmax,R,n):
        S=25.72*(2.88-R)**(-3.07)
        C=3.88e-9*S
        if self.pfm:#PFM計算のときには，正規乱数を発生してCに割り当てる
            mean=C
            std_dev=C*self.cov
            C=np.random.normal(mean,std_dev)
        self.C=C
        self.data['a']=a0
        self.data['c']=c0
        self.data['P']=Pmax
        self.cls.SetData(self.data)
        self.cls.Calc()
        res0=self.cls.GetRes()
        a=a0
        c=c0
        for i in range(n):
            da,dc,resMax=self.dadN(a,c,Pmin,Pmax)
            a += da/1000
            c += dc/1000
        crack={'a':a,
               'c':c}
        res1=resMax
        return res0,res1,crack
        
        
class Treat:
    def Set(self,spec:str):
        '''
        対象とする解析記号名を文字列でセット
        '''
        spec2=spec.replace("-","_")
        df=self.Registered()
        dd=df[spec2[0]]
        if spec2 not in dd:
            print(spec+' is not registered yet!')
            return
        cls=globals()[spec2]
        instance=cls()
        return instance
    def Registered(self):
        df={'J':[
            'J_1_a',
            'J_1_b',
            'J_1_d',
            'J_1_e',
            'J_2_a',
            'J_2_b',
            'J_2_e',
            'J_2_f',
            'J_2_g_a',
            'J_2_g_b',
            'J_2_h',
            'J_2_k_a',
            'J_2_m',
            'J_2_k_b', 不明点
            'J_7_a'
            ],
            'K':[
            'K_1_a_1',
            'K_1_a_2',
            'K_1_a_3',
            'K_1_b_1',
            'K_1_c_1',
            'K_1_d_1',
            'K_1_d_2',
            'K_1_e_1',
            'K_1_e_2',
            'K_1_e_3',
            'K_2_a_1',
            'K_2_a_2',
            'K_2_a_3',
            'K_2_b_1',
            'K_2_b_2',
            'K_2_c_1',
            'K_2_c_2',
            'K_2_d',
            'K_2_e_1',
            'K_2_e_2',
            'K_2_e_3',
            'K_2_f_1',
            'K_2_f_2',
            'K_2_f_3',
            'K_2_g',
            'K_2_h_1',
            'K_2_h_2',
            'K_2_i_1',
            'K_2_i_2',
            'K_2_j',
            'K_2_k_1',
            'K_2_k_2',
            'K_2_k_3',
            'K_2_k_4',
            'K_2_l',
            'K_3_a',
            'K_3_b_1',
            'K_3_b_2',
            'K_3_c',
            'K_4_a_1', 
            'K_4_a_2',
            'K_4_b_1',
            'K_4_b_2',
            'K_4_c',
            'K_4_d',
            'K_4_e',
            'K_5_a',
            'K_5_b_1',
            'K_5_b_2',
            'K_5_b_3',
            'K_6_a',
            'K_6_b',
            'K_6_c',
            'K_7_a',
            'K_7_b',
            'K_7_c',
            'K_7_d',
            'K_7_e',
            'K_7_f',
            'K_8_a',
            'K_8_b',
            'K_8_c',
            'K_8_d'],
            'L':[
            'L_1_a',
            'L_1_b',
            'L_1_c',
            'L_1_d',
            'L_1_e',
            'L_2_a',
            'L_2_b',
            'L_2_c',
            'L_2_d',
            'L_2_e',
            'L_2_k',
            'L_3_b',
            'L_6_c',
            'L_7_b'
        ]
        }
        return df
from FFSeval import Kriging as kr
import csv
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Tuple
import importlib.resources as pkg_resources
from importlib import resources
from FFSeval import data
from typing import List, Union

RowType = Union[str, List[str]]
class dmanage:
    '''
    係数が表形式で与えられるときに，表データをcsvファイルから読み取り，
    Kriging法で内挿した上で，評価値を返す
    [使用法]二次元の場合*****************************
    dm=dmanage()
    data=dm.Finput('J-2-k-b.csv')
    X,W=dm.CSV2XW(data,1)
    r2_score=dm.KrigCalc(X,W)
    dm.DrawRes(X,W) #鳥観図による確認
    x_val=0.5; y_val=2.0 #評価したい点
    target_point=np.array([[x_val,y_val]])
    w_pred,sigma=dm.Eval(target_point)# w_predが予測値
    [使用法]三次元の場合*****************************
    dm=dmanage()
    data=dm.Finput('J-2-k-b.csv')
    z=[0.0625,0.125,0.25,0.37,0.50]#三次元目のデータリスト(表の数だけ存在)
    X,W=dm.Fconv3D(data,z)
    r2_score=dm.KrigCalc(X,W)
    target_point=np.array([[0.5,2,0.18]])
    w_pred,sigma=dm.Eval(target_point)# w_predが予測値
    '''
    def __init__(self):
        self.df=None
    def Fconv3D(self,data:list,z:list)->Tuple[np.ndarray, np.ndarray]:
        '''
        3次元の入力テーブルに対する対応
        dataの中から，全データの処理を行いX,Wを構成して戻す
        三次元目の情報はz:listで与える
        '''
        # STARTを含む要素の数をカウント
        count = 0
        for sublist in data:
            for item in sublist:
                if "START" in item:
                    count += 1
        nz=len(z)
        if count!=nz:
            print(f'STARTの数{count}とzのサイズ{nz}が一致していない')
            return
        W=np.array([])
        X=np.empty((0,3))
        for i in range(count):
            ith=i+1
            df=self.dRead(data,ith)
            xval=df['xval']
            yval=df['yval']
            xn=len(xval)
            yn=len(yval)
            for iy in range(yn):
                for ix in range(xn):
                    d=[yval[iy],xval[ix],z[i]]
                    X=np.append(X,[d], axis=0)
                    W=np.append(W,df['arr'][iy,ix])
        return X,W
    def Fconv4D(self,data:list,z1:list,z2:list)->Tuple[np.ndarray, np.ndarray]:
        '''
        4次元の入力テーブルに対する対応
        dataの中から，全データの処理を行いX,Wを構成して戻す
        三次元目，四次元目の情報はz1:list,z2:listで与える
        '''
        # STARTを含む要素の数をカウント
        count = 0
        for sublist in data:
            for item in sublist:
                if "START" in item:
                    count += 1
        nz1=len(z1)
        nz2=len(z2)
        if count!=nz1 or count!=nz2:
            print(f'STARTの数{count}とzのサイズ{nz1,nz2}が一致していない')
            return
        W=np.array([])
        X=np.empty((0,4))
        for i in range(count):
            ith=i+1
            df=self.dRead(data,ith)
            xval=df['xval']
            yval=df['yval']
            xn=len(xval)
            yn=len(yval)
            for iy in range(yn):
                for ix in range(xn):
                    d=[yval[iy],xval[ix],z1[i],z2[i]]
                    X=np.append(X,[d], axis=0)
                    W=np.append(W,df['arr'][iy,ix])
        return X,W
    def extract_1D(self,data: List[RowType], block_index:int):
        '''一次元データの抽出
        block_index: 抽出したいブロック番号
        '''
        dm=dmanage()
        dd=dm.extract_block(data,block_index)
        str_list=dd[3]
        X = [float(x) for x in str_list]
        Y=[]
        for i in range(4,len(X)+4):
            Y.append(float(dd[i][0]))
        return X,Y 
    def extract_block(self,
        data: List[RowType], ith: int,
        start_token: str = 'START',
        end_token: str = 'END'
    ) -> List[List[str]]:
        """
        data: 行のリスト。各要素は「文字列」または「セルのリスト」のどちらでもOK。
            文字列ならCSV風にsplit(','), リストならそのまま扱う。
        ith : 取り出したい START ブロックの番号（1始まり）
        戻り値：START 行から END 行まで（START/END を含む）を二次元リストで返す。
        """
        count = 0
        collecting = False
        block: List[List[str]] = []

        for line in data:
            # 文字列 or リストの両対応
            if isinstance(line, str):
                row = [c.strip() for c in line.split(',')]
            elif isinstance(line, list):
                row = [str(c).strip() for c in line]
            else:
                raise TypeError(f"Unsupported row type: {type(line)}")

            # START 判定
            if row and row[0] == start_token:
                count += 1
                collecting = (count == ith)
                if collecting:
                    block.append(row)  # ★ START 行も含める
                continue

            if collecting:
                block.append(row)
                # END 行で終了（END も含めた上で break）
                if row and row[0] == end_token:
                    break

        return block            
    def Finput(self,fname:str)->list:
        '''
        csvファイルを読み取りリストに格納する
        '''
#        with resources.files("FFSeval.data").joinpath("J-2-k-a-2.csv").open("r", encoding="utf-8", newline='') as csvfile:
        with resources.files("FFSeval.data").joinpath(fname).open("r", encoding="utf-8", newline='') as csvfile:

            reader = csv.reader(csvfile)

            data=[]
            for row in reader:
                data.append(row)
        return data        
    def dRead(self,data:list,ith:int)->dict:
        '''
        dataのith番目のテーブルを辞書として返す
        '''
        n=len(data)
        ii=0
        flag=False
        res=[]
        l=0
        for ll in data:
            if ll[0]=='START':
                ii+=1
                if ii==ith:
                    flag=True
                    l+=1
                    continue
            if flag and l!=0:
                if ll[0]=='END':
                    break
                if l==1:
                    nx=int(ll[0])
                    ny=int(ll[1])
                    l+=1
                    continue
                if l==2:
                    numlist=[float(x) for x in ll[:nx]]
                    #numlist = [float(x) if x.strip() != '' else 0.0 for x in ll[:nx]]
                    xval=numlist
                    l+=1
                    continue
                if l==3:
                    numlist=[float(x) for x in ll[:ny]]
                    #numlist = [float(x) if x.strip() != '' else 0.0 for x in ll[:ny]]
                    yval=numlist
                    l+=1
                    continue
                numlist=[float(x) for x in ll[:nx]]
                #numlist = [float(x) if x.strip() != '' else 0.0 for x in ll[:nx]]
                res.append(numlist)
                l+=1
        arr=np.array(res)
        df={}
        df['xval']=xval
        df['yval']=yval
        df['arr']=arr
        return df
    def MakeInp(self,df:dict)->Tuple[np.ndarray, np.ndarray]:
        '''
        辞書型データを，Kriging入力用のnp.arrayに変換する
        '''
        xval=df['xval']
        yval=df['yval']
        xn=len(xval)
        yn=len(yval)
        W=np.array([])
        X=np.empty((0,2))
        for iy in range(yn):
            for ix in range(xn):
                d=[yval[iy],xval[ix]]
                X=np.append(X,[d], axis=0)
                W=np.append(W,df['arr'][iy,ix])
        return X,W
    def CSV2XW(self,data:list,ith:int)->Tuple[np.ndarray, np.ndarray]:
        df=self.dRead(data,ith)
        X,W=self.MakeInp(df)
        self.df=df
        return X,W
    def GetDf(self):
        return self.df
    def KrigCalc(self,X,W,alpha=5e-4):
        self.krig=kr.Kriging()
        self.krig.setData(X,W)
        r2_score=self.krig.Fit(alpha=alpha)
        return r2_score
    def Eval(self,target_point:np.array)->float:
        #target_point = np.array([[x, y]])  
        w_pred,sigma=self.krig.Predict(target_point)
        return w_pred[0],sigma        
    def DrawRes(self,X,W)->None:
        # 1. 描画用のメッシュグリッドを作成
        x = np.linspace(np.min(X[:,0]), np.max(X[:,0]), 50)
        y = np.linspace(np.min(X[:,1]), np.max(X[:,1]), 50)
        X_grid, Y_grid = np.meshgrid(x, y)

        # 2. メッシュ座標を一次元にして予測
        XY = np.vstack([X_grid.ravel(), Y_grid.ravel()]).T

        # Kriging モデルで予測（タプルで返る）
        Z_pred, _ = self.krig.Predict(XY)

        # 予測値をグリッド形状に整形
        Z_grid = Z_pred.reshape(X_grid.shape)

        # 4. 描画
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        # 予測面
        ax.plot_surface(X_grid, Y_grid, Z_grid, cmap='viridis', alpha=0.7)

        # 元データ点も重ねる
        #ax.scatter(X[:,0], X[:,1], W, color='r', s=30, label='Data points')
        # 予測に使ったデータ点を赤い球で表示
        ax.scatter(X[:, 0], X[:, 1], W, color='black', s=30, marker='^', label='Training data')
        # 軸ラベル
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('W')

        # タイトル・凡例
        ax.set_title('Kriging Model Surface')
        ax.legend()
        plt.show()
#------------------------------------------------------------------

from FFSeval import FFS as ffs
class J_1_a(Base):
    def __init__(self):
        super().SetTitle('半楕円表面き裂 三浦らの解')

        super().SetRefer(
            "三浦，島川，中山，高橋：高温下における欠陥評価のためのJ積分簡易解析法の体系化，材料，Vol.49，No.8，pp.845-850，2000 / "
            "島川，三浦，中山，高橋：高温下における欠陥評価のためのJ積分簡易解析法の適用性検証，材料，Vol.49，No.8，pp.851-856，2000"
        )

        # Applicable range: Kの適用範囲については，K-1-aを参照．

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half crack length
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # tensile load
        M = df['M']          # bending moment
        E = df['E']          # Young's modulus
        nu = df['Nu']        # Poisson's ratio
        alpha = df['alpha']  # Ramberg-Osgood alpha
        n = df['n']          # Ramberg-Osgood n
        Sy = df['Sy']        # yield stress

        sigma_m = P / (2.0 * b * t)
        sigma_b = 3.0 * M / (b * t ** 2)


        sigma_mK = sigma_m

        sigma0 = Sy
        x = sigma_b / sigma0
        numer = x ** 3 + (3.0 * (n + 1.0) / (n + 2.0)) * alpha * x ** (n + 2.0) + (3.0 * n / (2.0 * n + 1.0)) * (alpha ** 2) * x ** (2.0 * n + 1.0)
        denom = (x + alpha * x ** n) ** 2
        sigma_bK = (numer / denom) * sigma0

        # 膜応力 sigma_mK および曲げ応力 sigma_bK により、K-1-a-1 からKA,KBを算出
        Pk = sigma_mK * (2.0 * b * t)
        Mk = sigma_bK * (b * t ** 2) / 3.0

        cls = ffs.Treat()
        K = cls.Set('K-1-a-1')
        K.SetData({'a': a, 'c': c, 'b': b, 't': t, 'P': Pk, 'M': Mk})
        K.Calc()
        kres = K.GetRes()
        KA = kres['KA']
        KB = kres['KB']

        JAe = (KA ** 2) * (1.0 - nu ** 2) / E
        JBe = (KB ** 2) * (1.0 - nu ** 2) / E

        zeta = a * c / (t * (c + t))
        g = 1.0 - 20.0 * (zeta**3) * (a / (2.0 * c))**0.75
        sigma_ref = (g * sigma_b / 3.0 + np.sqrt((g**2) * (sigma_b**2) / 9.0 + (1.0 - zeta)**2 * (sigma_m**2))) / (1.0 - zeta)**2
        epsilon_ref = (Sy / E) * ((sigma_ref / Sy) + alpha * (sigma_ref / Sy)**n)
        F = E * epsilon_ref / sigma_ref

        # 最深点
        JA = F * JAe
        # 表面点
        JB = F * JBe

        res = {
            'JA': JA,
            'JB': JB,
        }
        super().SetRes(res) 


class J_1_b(Base):
    def __init__(self):
        super().SetTitle('長い表面き裂(片側) Kumar らの解')

        super().SetRefer(
            "Kumar, V., German, M. D., and Shih, C. F.: An Engineering Approach for Elastic-Plastic Fracture Analysis, EPRI NP-1931, 1981"
        )

        # K の適用範囲については 3章K の K-1-b 参照.

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        c = df['c']          # half surface length
        L = df['L']          # length
        b = df['b']          # half width
        P = df['P']          # load
        S0 = df['S0']        # stress
        E = df['E']          # Young's modulus
        nu = df['Nu']        # Poisson's ratio
        plane = df['plane']
        alpha = df['alpha']
        n = df['n']
        epsilon0 = df['epsilon0']

        data = dm.Finput('J-1-b.csv')
        target_point = np.array([[a / t, n]])
        H1 = np.zeros(2, dtype=float)
        for ith in range(1, 3):                 # 1,2  (→ 平面応力、平面歪)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            H1[ith - 1] = float(Fi)

        if plane == 'stress':
            Ht = H1[0]
        if plane == 'strain':
            Ht = H1[1]

        #data = dm.Finput('J-1-b-2.csv')
        target_point = np.array([[a / t, n]])
        H1 = np.zeros(2, dtype=float)
        for ith in range(3, 5):                 # 3,4  (→ 平面応力、平面歪)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            H1[ith - 3] = float(Fi)

        if plane == 'stress':
            Hb = H1[0]
        if plane == 'strain':
            Hb = H1[1]

        M = P * L / 2.0

        cls = ffs.Treat()
        K1b1 = cls.Set('K-1-b-1')
        K1b1.SetData({'a': a, 'b': b, 't': t, 'P': P, 'M': M})
        K1b1.Calc()
        K = K1b1.GetRes()
        if isinstance(K, dict):
            if 'K' in K:
                K = K['K']
            elif 'KA' in K:
                K = K['KA']

        ac = a / c
        at = a / t
        eta = np.sqrt(1.0 + ac**2) - ac

        if plane == 'stress':
            beta = 2.0
            Eprime = E
            P0_tension = 1.072 * eta * c * S0
            P0_bending = 0.536 * S0 * (c**2) / L
        if plane == 'strain':
            beta = 6.0
            Eprime = E / (1.0 - nu**2)
            P0_tension = 1.445 * eta * c * S0
            P0_bending = 0.728 * S0 * (c**2) / L

        gamma_y = (1.0 / (beta * np.pi)) * ((n - 1.0) / (n + 1.0)) * (K / S0)**2
        phi_t = 1.0 / (1.0 + (P / P0_tension)**2)
        ae_t = a + phi_t * gamma_y
        phi_b = 1.0 / (1.0 + (P / P0_bending)**2)
        ae_b = a + phi_b * gamma_y

        Jt = (K * ae_t**2) / Eprime + alpha * S0 * epsilon0 * c * at * Ht * (P / P0_tension)**(n + 1.0)
        Jb = (K * ae_b**2) / Eprime + alpha * S0 * epsilon0 * c * at * Hb * (P / P0_bending)**(n + 1.0)

        res = {'Jt': Jt, 'Jb': Jb}
        super().SetRes(res)

class J_1_d(Base):
    def __init__(self):
        super().SetTitle('貫通き裂 Kumar らの解')

        super().SetRefer(
            "Kumar, V., German, M. D., and Shih, C. F.: An Engineering Approach for Elastic-Plastic Fracture Analysis, EPRI NP-1931, 1981"
        )

        # K の適用範囲については 3章K の K-1-d 参照.

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # half crack length
        b = df['b']          # half width
        c = df['c']          # half ligament length
        t = df['t']          # thickness
        P = df['P']          # load
        S0 = df['S0']        # stress
        E = df['E']          # Young's modulus
        nu = df['Nu']        # Poisson's ratio
        plane = df['plane']
        alpha = df['alpha']
        n = df['n']
        epsilon0 = df['epsilon0']

        data = dm.Finput('J-1-d.csv')
        target_point = np.array([[a / b, n]])
        H1 = np.zeros(2, dtype=float)
        for ith in range(1, 3):                 # 1,2  (→ 平面応力、平面歪)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            H1[ith - 1] = float(Fi)

        if plane == 'stress':
            H = H1[0]
        if plane == 'strain':
            H = H1[1]

        cls = ffs.Treat()
        K = cls.Set('K-1-d-1')
        K.SetData({'t': t, 'c': c, 'b': b, 'P': P, 'M': 0}) #モーメント=0
        K.Calc()
        kres = K.GetRes()
        KA = kres['KA']
        KB = kres['KB']

        if plane == 'stress':
            beta = 2.0
            Eprime = E
            P0 = 2.0 * c * S0
        if plane == 'strain':
            beta = 6.0
            Eprime = E / (1.0 - nu**2)
            P0 = 4.0 * c * S0 / np.sqrt(3.0)

        phi = 1.0 / (1.0 + (P / P0)**2)

        gamma_ya = (1.0 / (beta * np.pi)) * ((n - 1.0) / (n + 1.0)) * (KA / S0)**2
        gamma_yb = (1.0 / (beta * np.pi)) * ((n - 1.0) / (n + 1.0)) * (KB / S0)**2
        ae_a = a + phi * gamma_ya
        ae_b = a + phi * gamma_yb

        JA = (KA * ae_a**2) / Eprime + alpha * S0 * epsilon0 * a * (c / b) * H * (P / P0)**(n + 1.0)
        JB = (KB * ae_b**2) / Eprime + alpha * S0 * epsilon0 * a * (c / b) * H * (P / P0)**(n + 1.0)

        res = {
            'JA': JA,
            'JB': JB,
        }
        super().SetRes(res)

class J_1_e(Base):
    def __init__(self):
        super().SetTitle('楕円内部き裂　半楕円表面き裂へのモデル化（三浦らの解の拡張）')

        super().SetRefer(
            "三浦，島川，中山，高橋：高温下における欠陥評価のための J 積分簡易解析法の体系化，材料，Vol.49，No.8，pp.845-850，Aug.2000\n"
            "島川，三浦，中山，高橋：高温下における欠陥評価のための J 積分簡易解析法の適用性検証，材料，Vol.49，No.8，pp.851-856，Aug.2000"
        )

        # K の適用範囲については，3章 K の K-1-a を参照。

    def Calc(self):
        df = super().GetData()

        a = df['a']          # half crack depth
        b = df['b']          # half width
        c = df['c']          # half crack length
        t = df['t']          # thickness
        P = df['P']          # tensile load

        t2 = t / 2.0
        P2 = P / 2.0

        # J-1-a（半楕円表面き裂）の解を参照して J を算出
        cls = ffs.Treat()
        J1a = cls.Set('J-1-a')
        J1a.SetData({
            'a': a,
            'c': c,
            't': t2,
            'b': b,
            'P': P2,         
            # 以降は J-1-a 側で必要な値をそのまま渡す（本クラスでは新規定義しない）
            'M': df['M'],
            'E': df['E'],
            'Nu': df['Nu'],
            'alpha': df['alpha'],
            'n': df['n'],
            'Sy': df['Sy'],
        })

        J1a.Calc()
        J = J1a.GetRes()
        res = {'J': J}
        super().SetRes(res)

            
class J_2_k_a(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['theta','plane','M','R','t','P','S0','alpha','e0','n','E','Case'])
        super().SetTitle('周方向貫通亀裂 Zahoorの解')
        super().SetRefer('Zahoor, A.:Ductile Fracture Handbook Volume 1,EPRI NP-6301-D,1989')
        # Kriging法による応答曲面を計算
        self.dm_P=dmanage()
        data=self.dm_P.Finput('J-2-k-a-1.csv')
        z=[5.0,10.0,20.0]
        X,W=self.dm_P.Fconv3D(data,z)
        r2_score=self.dm_P.KrigCalc(X,W)
        self.dm_M=dmanage()
        data=self.dm_M.Finput('J-2-k-a-2.csv')
        z=[5.0,10.0,20.0]
        X,W=self.dm_M.Fconv3D(data,z)
        r2_score=self.dm_M.KrigCalc(X,W)                  
    def Calc(self):
        df=super().GetData()
        th=df['theta']
        plane=df['plane']
        if plane=='stress': beta=2
        if plane=='strain': beta=6
        M=df['M']
        R=df['R']
        t=df['t']
        P=df['P']
        S0=df['S0']
        alpha=df['alpha']
        e0=df['e0']
        n=df['n']
        E=df['E']
        A=0.0
        P0=2.0*S0*R*t*(np.pi-th-2.0*np.arcsin(0.5*np.sin(th))) 
        M0=4.0*S0*R*R*t*(np.cos(th/2.0)-0.5*np.sin(th))
        if df['Case']=='Collapse': #塑性崩壊値の計算
            res={
                'P0':P0,
                'M0':M0
            }
            super().SetRes(res)
            return
        if R/t >= 5.0 and R/t<10.0:
            A=(0.125*(R/t)-0.25)**0.25
        if R/t>=10.0 and R/t<=20.0:
            A=(0.4*R/t-3.0)**0.25
        if plane=='stress': beta=2
        if plane=='strain': beta=6
        if df['Case']=='PR': #塑性崩壊強度の計算
            pass #将来開発すること
        if df['Case']=='PJ':
            target_point=np.array([[th/np.pi,n,R/t]])
            H1,sigma=self.dm_P.Eval(target_point)           
            Ft=1.0+A*(5.3303*(th/np.pi)**1.5+18.773*(th/np.pi)**4.24)
            St=P/(2.0*np.pi*R*t)
            the=th*(1.0+(Ft*Ft/beta)*(n-1)/(n+1)*(St/S0)**2/(1+(P/P0)**2))
            ft=(the/np.pi)*(1.0+A*(5.3303*(the/np.pi)**1.5+18.773*(the/np.pi)**4.24))**2
            J=ft*P*P/(4.0*np.pi*R*t*t*E)+alpha*S0*e0*(np.pi-th)*H1*(P/P0)**(n+1)
            res={'J':J}
            super().SetRes(res)
            return
        if df['Case']=='MR': #塑性崩壊強度の計算
            target_point=np.array([[th/np.pi,n,R/t]])
            H1,sigma=self.dm_M.Eval(target_point)
            JR=df['JR']
            MR=M0*(JR/(alpha*S0*e0*np.pi*R*(1.0-th/np.pi)**2*H1))**(1./(n+1.))
            res={'MR':MR,
                    'M0':M0,
                    'H1':H1}
            super().SetRes(res)
            return
        if df['Case']=='MJ':
            target_point=np.array([[th/np.pi,n,R/t]])
            H1,sigma=self.dm_M.Eval(target_point)
            Sb=M/(np.pi*R*R*t)

            Fb=1.0+A*(4.5967*(th/np.pi)**1.5+2.6422*(th/np.pi)**4.24)
            the=th*(1.0+Fb*Fb/beta*(n-1)/(n+1)*(Sb/S0)**2/(1+(M/M0)**2))
            fb=(the/np.pi)*(1.0+A*(4.5967*(the/np.pi)**1.5+2.6422*(the/np.pi)**4.24))**2
            J=fb*M*M/(R*R*R*t*t*E)+alpha*S0*e0*np.pi*R*(1-th/np.pi)**2*H1*(M/M0)**(n+1) 
            res={'J':J,
                'M0':M0,
                'H1':H1}
            super().SetRes(res)
class J_2_a(Base):
    def __init__(self):
        super().SetTitle('軸方向内表面半楕円表面き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 3, EPRI NP-6301-D, 1991"
        )

        # Applicable range: 1/40 ≤ a/(2c) ≤ 1/3, 0.1 ≤ a/t ≤ 0.8, 0.2 ≤ α, Ri/t = 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        c  = df['c']          # half surface length
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        p  = df['p']          # internal pressure
        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']    # Ramberg-Osgood parameter
        n        = df['n'] 
        sigma0   = df['sigma0']  
        epsilon0 = df['epsilon0'] 

        data = dm.Finput('J-2-a.csv')
        z = [1, 2, 3, 5, 7] # n
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, a / (2.0 * c), n]])
        H1,sigma=dm.Eval(target_point)

        sigma_h = (2.0 * p * (Ro ** 2)) / ((Ro ** 2) - (Ri ** 2)) 
        alpha1 = (a / t) / (a / c) ** 0.58
        F = 0.25 + 0.4759 * alpha1 + 0.1262 * alpha1 ** 2
        x = a / t
        B1 = np.sqrt(1.0 + 0.1533 * (c / t) ** 2)
        B0 = 1.0453 * ((1.0 - x / B1) / (1.0 - x))
        alpha_e = ((a / t) + (F ** 2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_h / sigma0) ** 2) / (1.0 + B0 * (sigma_h / sigma0) ** 2))) / (a / c) ** 0.58
        f = (0.25 + 0.4759 * alpha_e + 0.1262 * alpha_e ** 2) ** 2
        Eprime = E / (1.0 - nu ** 2) 

        J = (np.pi * t * f * (sigma_h ** 2) / Eprime + alpha * sigma0 * epsilon0 * t * H1 * (sigma_h / sigma0) ** (n + 1.0))

        res = {'J': J}
        super().SetRes(res)
class J_2_b(Base):
    def __init__(self):
        super().SetTitle('軸方向内表面長いき裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook, Volume 3 EPRI NP-6301-D, 1991"
        )

        # Applicable range: 0.05 <= a/t <= 0.8, 5 <= Ri/t <= 20

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        p  = df['p']          # internal pressure
        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']    # Ramberg-Osgood parameter
        n        = df['n'] 
        sigma0   = df['sigma0']  
        epsilon0 = df['epsilon0'] 

        data = dm.Finput('J-2-b.csv')
        z = [1,2,5] # Ri/t
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, n, Ri/t]])
        H1,sigma=dm.Eval(target_point)

        sigma_h = (2.0 * p * (Ro ** 2)) / ((Ro ** 2) - (Ri ** 2))

        if (Ri / t) <= 10.0:
            A = (0.125 * (Ri / t) - 0.25) ** 0.25
        if (Ri / t) > 10.0:
            A = (0.2 * (Ri / t) - 1.0) ** 0.25

        B0 = (3.0 / 16.0) * (1.0 - (Ri**2) / (Ro**2)) * ((Ri / t) + (a / t)) / (1.0 - (a / t))**2
        F = 1.1 + A * (4.951 * (a / t)**2 + 1.092 * (a / t)**4)
        ae_over_t = (a / t) * (1.0 + (F**2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_h / sigma0)**2) / (1.0 + B0 * (sigma_h / sigma0)**2)))
        f = (ae_over_t) * (1.1 + A * (4.951 * (ae_over_t)**2 + 1.092 * (ae_over_t)**4))**2
        Eprime = E / (1.0 - nu ** 2)

        J = np.pi * t * f * (sigma_h**2) / Eprime + alpha * sigma0 * epsilon0 * t * H1 * (sigma_h / sigma0)**(n + 1.0)

        res = {'J': J}
        super().SetRes(res)
class J_2_e(Base):
    def __init__(self):
        super().SetTitle('軸方向貫通き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0 < lambda_ <= 5, sigma < sigma_f / M

    def Calc(self):
        df = super().GetData()

        c = df['c']          # half surface length
        t = df['t']          # wall thickness
        R = df['R']          # mean radius
        p = df['p']          # internal pressure
        E = df['E']          # Young's modulus
        sigma_f = df['sigma_f']

        lambda_ = c / np.sqrt(R * t)
        M = np.sqrt( 1.0 + 1.2987 * lambda_ ** 2 - 0.026905 * lambda_ ** 4 + 5.3549e-4 * lambda_ ** 6)
        sigma = p * R / t

        J = (8.0 * c * (sigma_f ** 2) / (np.pi * E)) * np.log(1.0 / np.cos(M * np.pi * sigma / (2.0 * sigma_f)))

        res = {'J': J}
        super().SetRes(res)
class J_2_f(Base):
    def __init__(self):
        super().SetTitle('周方向内表面半楕円表面き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0.05 ≤ (theta/pi) ≤ 1, 0.10 ≤ a/t ≤ 0.80, R/t = 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        c  = df['c']          # half surface length
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        P  = df['P']          # axial load
        R  = df['R']          # mean radius

        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']    # Ramberg-Osgood parameter
        n        = df['n']
        sigma0   = df['sigma0']
        epsilon0 = df['epsilon0']

        theta = np.pi * c / (4.0 * Ri)

        data = dm.Finput('J-2-f.csv')
        z = [1, 2, 5, 10] # n
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, theta / np.pi, n]])
        H1,sigma=dm.Eval(target_point)

        sigma_t = P / (2.0 * np.pi * R * t)
        A0 = (0.25 + a / c) ** 0.58
        Rc = Ri + a
        B0 = (2.0 * R * t / (Ro ** 2 - Rc ** 2 + (1.0 - theta / np.pi) * (Rc ** 2 - Ri ** 2))) ** 2

        x = a / t
        if (x / A0) >= 0.25:
            Ft = 0.25 + 0.5298 * (x / A0) + 0.3835 * (x / A0) ** 2
        if (x / A0) < 0.25:
            Ft = 3.72 * (x / A0) - 13.475 * (x / A0) ** 2 + 19.988 * (x / A0) ** 3

        ae_over_t = (a / t) + (Ft ** 2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_t / sigma0) ** 2) / (1.0 + (sigma_t / sigma0) ** 2 * B0))

        if (ae_over_t / A0) >= 0.25:
            ft = (0.25 + 0.5298 * (ae_over_t / A0) + 0.3835 * (ae_over_t / A0) ** 2) ** 2
        if (ae_over_t / A0) < 0.25:
            ft = (3.72 * (ae_over_t / A0) - 13.475 * (ae_over_t / A0) ** 2 + 19.988 * (ae_over_t / A0) ** 3) ** 2

        Eprime = E / (1.0 - nu ** 2)

        J = (ft * P ** 2) / (4.0 * np.pi * (R ** 2) * t * Eprime) + alpha * sigma0 * epsilon0 * t * H1 * (sigma_t / sigma0) ** (n + 1.0)

        res = {'J': J}
        super().SetRes(res)
class J_2_g_a(Base):
    def __init__(self):
        super().SetTitle('周方向内表面扇形表面き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0.05 ≤ (theta/pi) ≤ 1.0, 0.10 ≤ a/t ≤ 0.80, R/t = 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        c  = df['c']          # half surface length
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        P  = df['P']          # axial load
        R  = df['R']          # mean radius

        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']    # Ramberg-Osgood parameter
        n        = df['n']
        sigma0   = df['sigma0']
        epsilon0 = df['epsilon0']

        theta = c / Ri

        data = dm.Finput('J-2-g-a.csv')
        z = [1, 2, 5, 10] # n
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, theta / np.pi, n]])
        H1,sigma=dm.Eval(target_point)

        sigma_t = P / (2.0 * np.pi * R * t)
        Rc = Ri + a
        B0 = (2.0 * R * t / (Ro ** 2 - Rc ** 2 + (1.0 - theta / np.pi) * (Rc ** 2 - Ri ** 2))) ** 2
        x = a / t
        Ft = 1.1 + x * (0.15241 + 16.772 * (x * theta / np.pi) ** 0.855 - 14.944 * (x * theta / np.pi))
        ae = a * (1.0 + (Ft ** 2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_t / sigma0) ** 2) / (1.0 + (sigma_t / sigma0) ** 2 * B0)))
        ae_over_t = ae / t
        ft = (ae_over_t) * (1.1 + ae_over_t * (0.15241 + 16.772 * (ae_over_t * theta / np.pi) ** 0.855 - 14.944 * (ae_over_t * theta / np.pi))) ** 2
        Eprime = E / (1.0 - nu ** 2)
        J = (ft * P ** 2) / (4.0 * np.pi * (R ** 2) * t * Eprime) + alpha * sigma0 * epsilon0 * t * H1 * (sigma_t / sigma0) ** (n + 1.0)

        res = {'J': J}
        super().SetRes(res)
class J_2_g_b(Base):
    def __init__(self):
        super().SetTitle('内表面の周方向扇形表面き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0.05 ≤ (theta/pi) ≤ 0.7, 0.10 ≤ a/t ≤ 0.80, R/t = 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        c  = df['c']          # half surface length
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        R  = df['R']          # mean radius
        M  = df['M']          # bending moment

        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']
        n        = df['n']
        sigma0   = df['sigma0']
        epsilon0 = df['epsilon0']

        theta = c / Ri

        data=dm.Finput('J-2-g-b.csv')
        z = [1,2,5] # n
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, theta / np.pi, n]])
        H1,sigma=dm.Eval(target_point)

        I = np.pi * (Ro ** 4 - Ri ** 4) / 4.0
        sigma_b = M * R / I
        x = a / t
        beta = 0.5 * np.pi * (1.0 - x * theta / np.pi)
        B0 = (I / (4.0 * (R ** 3) * t * (np.sin(beta) - 0.5 * x * np.sin(theta)))) ** 2
        Fb = 1.1 + x * (-0.09967 + 5.0057 * (x * theta / np.pi) ** 0.565 - 2.8329 * (x * theta / np.pi))
        ae = a * (1.0 + (Fb ** 2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_b / sigma0) ** 2) / (1.0 + (sigma_b / sigma0) ** 2 * B0)))
        ae_over_t = ae / t
        fb = (ae_over_t) * (1.1 + ae_over_t * (-0.09967 + 5.0057 * (ae_over_t * theta / np.pi) ** 0.565 - 2.8329 * (ae_over_t * theta / np.pi))) ** 2
        Eprime = E / (1.0 - nu ** 2)

        J = (fb * M ** 2) / (np.pi * (R ** 4) * t * Eprime) + alpha * sigma0 * epsilon0 * t * H1 * (sigma_b / sigma0) ** (n + 1.0)

        res = {'J': J}
        super().SetRes(res)
class J_2_h(Base):
    def __init__(self):
        super().SetTitle('周方向内表面全周き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0.05 ≤ a/t ≤ 0.8, 5 ≤ Ri/t ≤ 20

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a  = df['a']          # crack depth
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        P  = df['P']          # axial load

        E  = df['E']          # Young's modulus
        nu = df['Nu']         # Poisson's ratio
        alpha    = df['alpha']
        n        = df['n']
        sigma0   = df['sigma0']
        epsilon0 = df['epsilon0']

        R = 0.5 * (Ri + Ro)
        Ri_t = Ri / t

        data = dm.Finput('J-2-h.csv')
        z = [5, 10, 20] # Ri_t
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a / t, n, Ri_t]])
        H1,sigma=dm.Eval(target_point)

        sigma_t = P / (2.0 * np.pi * R * t)
        P0 = (2.0 * np.pi / np.sqrt(3.0)) * sigma0 * (Ro ** 2 - (Ri + a) ** 2)

        if Ri_t <= 10.0:
            A = (0.125 * Ri_t - 0.25) ** 0.25
        if Ri_t > 10.0:
            A = (0.4 * Ri_t - 3.0) ** 0.25

        F = 1.1 + A * (1.948 * (a / t) ** 1.5 + 0.3342 * (a / t) ** 4.2)
        ae = a * ( 1.0 + (F ** 2 / 6.0) * ((n - 1.0) / (n + 1.0)) * (((sigma_t / sigma0) ** 2) / (1.0 + (P / P0) ** 2)))
        ae_over_t = ae / t
        f = (ae_over_t) * ( 1.1 + A * (1.948 * ae_over_t ** 1.5 + 0.3342 * ae_over_t ** 4.2)) ** 2
        Eprime = E / (1.0 - nu ** 2)

        J = ( f * P ** 2 / (4.0 * np.pi * R ** 2 * t * Eprime) + alpha * sigma0 * epsilon0 * t * (1.0 - (a / t)) ** 2 * H1 * (P / P0) ** (n + 1.0))

        res = {'J': J}
        super().SetRes(res)

class J_2_k_b(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['theta','plane','M','R','t','P','S0','alpha','e0','n','E'])
        super().SetTitle('周方向貫通亀裂　Zahoorの解')
        super().SetRefer('Zahoor, A.:Ductile Fracture Handbook Volume 1,EPRI NP-6301-D,1989')

             
             
    def Calc(self):
        df=super().GetData()
        th=df['theta']/180.0*np.pi
        plane=df['plane']
        if plane=='stress': beta=2
        if plane=='strain': beta=6
        M=df['M']
        R=df['R']
        t=df['t']
        P=df['P']
        St=P/(2.*np.pi*R*t)
        Sb=M/(np.pi*R*R*t)
        S0=df['S0']
        P0=2*S0*R*t*(np.pi-th-2*np.arcsin(0.5*np.sin(th)))
        M0=4*S0*R*R*t*(np.cos(th/2)-0.5*np.sin(th))
        lam=M/P/R
        P0d=0.5*(-lam*R*P0*P0/M0+np.sqrt((lam*R*P0*P0/M0)**2+4*P0*P0))
        n=df['n']
        dm=dmanage()
        x=lam/(1.+lam)
        data=dm.Finput('J-2-k-b.csv')
        z=[0.0625,0.125,0.25,0.37,0.50]#三次元目のデータリスト(表の数だけ存在)
        X,W=dm.Fconv3D(data,z)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[x,n,th/np.pi]])
        h1,sigma=dm.Eval(target_point)
        E=df['E']
        alpha=df['alpha']
        e0=df['e0']
        if R/t > 5.0 and R/t <=10.0:
            A=(0.125*(R/t)-0.25)**0.25
        elif R/t>10.0 and R/t <=20.0:
            A=(0.4*(R/t)-3.0)**0.25
        Ft=1+A*(5.3303*(th/np.pi)**1.5+18.773*(th/np.pi)**4.24)
        Fb=1+A*(4.5967*(th/np.pi)**1.5+2.6422*(th/np.pi)**4.24)
        the=th*(1+(1/beta)*((n-1)/(n+1))*((St*Ft+Sb*Fb)**2/S0/S0)/(1+(P/P0d)**2))            
        ft=(the/np.pi)*(1+A*(5.3303*(the/np.pi)**1.5+18.773*(the/np.pi)**4.24))**2
        fb=(the/np.pi)*(1+A*(4.5967*(the/np.pi)**1.5+2.6422*(the/np.pi)**4.24))**2
        J=ft*P*P/(4*R*t*t*E)+fb*M*M/(R*R*R*t*t*E)+alpha*S0*e0*R*(np.pi-th)*(th/np.pi)*h1*(P/P0d)**(n+1)
        res={'J':J}
        super().SetRes(res)

class J_2_m(Base):
    def __init__(self):
        super().SetTitle('周方向内表面貫通と表面の複合き裂 Zahoor の解')
        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range: 0.1 ≤ theta/pi ≤ 0.6, 0.1 ≤ a/t ≤ 0.7, 5 ≤ R/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a     = df['a']        # crack depth
        theta = df['theta']    # half crack angle
        t     = df['t']        # wall thickness
        R     = df['R']        # mean radius
        M     = df['M']        # bending moment

        E        = df['E']         # Young's modulus
        n        = df['n']
        sigma0   = df['sigma0']
        epsilon0 = df['epsilon0']
        plane=df['plane']
        if plane=='stress': beta=2
        if plane=='strain': beta=6

        at = a / t
        Rt = R / t
        theta_pi = theta / np.pi

        data=dm.Finput('J-2-m.csv')
        z1=[  5,  5,  5,  5,  5,  5,  5, 10, 10, 10, 10, 10, 10, 10]
        z2=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.1,0.2,0.3,0.4,0.5,0.6,0.7]
        X,W=dm.Fconv4D(data,z1,z2)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[theta_pi, n, Rt, at]])
        H1,sigma=dm.Eval(target_point)

        A = (0.125 * Rt - 0.25) ** 0.25
        F0 = ((1.0 + at) * (1.0 - at) ** 2 * (1.0 + 0.5 * at / Rt)) ** (-0.5)
        sigma_b = M / (np.pi * (R ** 2) * t)
        M0 = 4.0 * sigma0 * (R ** 2) * t * (np.cos(theta / 2.0) - 0.5 * np.sin(theta))
        Fb = F0 * (1.0 + A * (4.5967 * (theta_pi ** 1.5) + 2.6422 * (theta_pi ** 4.24)))
        theta_e = theta * ( 1.0 + (Fb**2 / beta)*((n - 1.0) / (n + 1.0))*(((sigma_b / sigma0)**2) / (1.0 + (M / M0)**2)))
        theta_e_pi = theta_e / np.pi
        fb = theta_e_pi * (1.0 + A * (4.5967*(theta_e_pi**1.5) + 2.6422*(theta_e_pi**4.24)))**2 * (F0**2)

        J = fb*(M**2) / ((R**3)*(t**2)*E) + sigma0*epsilon0*np.pi*(R + a / 2.0)*(1.0 - theta_pi)**2*H1*(M / M0)**(n + 1.0)

        res = {'J': J}
        super().SetRes(res)

class J_7_a(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['a','R','alpha','n','sigma','sigma0','E'])
        super().SetTitle('円孔縁のき裂 片側貫通亀裂 Zahoorの解')
        super().SetRefer('Zahoor, A.:Ductile Fracture Handbook Volume 3,EPRI NP-6301-D,1991')  
    def Calc(self):
        dm=dmanage()
        df=super().GetData()

        a=df['a']
        R=df['R']
        alpha=df['alpha']
        n=df['n']
        S=df['sigma'] # σ 
        S0=df['sigma0'] # σ0
        E = df['E']
        e0=S0/E # ε0

        data=dm.Finput('J-7-a.csv')
        ith=1
        X,W=dm.CSV2XW(data,ith)
        r2_score=dm.KrigCalc(X,W)
        target_point=np.array([[a/R,n]]) 
        H1,sigma=dm.Eval(target_point) 

        a_over_R=a/R #代入してみましたが、代入するのとしないのとどちらが良いですか？  
        B0=(4.0/3.0)/(1-0.08696*(1+0.5*a_over_R))**2
        F=(2.8041-4.9327*a_over_R+7.986*a_over_R**2-6.9783*a_over_R**3+2.4132*a_over_R**4)
        ae=a*(1+0.5*F**2*((n-1)/(n+1))*((S/S0)**2/(1+B0*(S/S0)**2)))
        ae_over_R=ae/R #代入してみましたが、代入するのとしないのとどちらが良いですか？
        f=np.pi*ae_over_R*(2.8041-4.9327*ae_over_R+7.986*ae_over_R**2-6.9783*ae_over_R**3+2.4132*ae_over_R**4)**2
        #J=f*R*S**2/E+alpha*S0*e0*H1*(S/S0)**(n+1)
        J=f*R*S**2/E+alpha*S0*e0*R*H1*(S/S0)**(n+1) #R*が抜けていなした

        #res={'J':J,
            #'H1':H1}
        res={'J':J}#H1は戻す必要はありません
        super().SetRes(res) 


class K_1_a_1(Base):
    #by S.Sakai
    def __init__(self):
        super().SetTitle('平板の半楕円表面亀裂，Raju-Newmanの解')
        super().SetRefer('Newman,J.C>Jr., and Raju,I.S.:Stress-Intensity Factor Equations for Cracks in Three-Dimentional Finite Bodies Subjected to Tension and Bending Loads, NASA Technical Memorandum, 85793, NASA,1984')
        super().SetInputItems(['a','c','b','t','P','M'])
    def Calc(self):
        df=super().GetData()
        a=df['a']
        c=df['c']
        b=df['b']
        t=df['t']
        P=df['P']
        M=df['M']
        Sm=P/(2*b*t)
        Sb=3*M/(b*t*t)
        if a/c <=1.0:
            Q=1+1.464*(a/c)**1.65
            g=1
            fphai=1
            fw=np.sqrt(1.0/np.cos(np.pi*c/(2*b)*np.sqrt(a/t)))
            H=1+(-1.22-0.12*a/c)*a/t+(0.55-1.05*(a/c)**0.75+0.47*(a/c)**1.5)*(a/t)**2
            FA=(1.13-0.09*a/c+(-0.54+0.89/(0.2+a/c))*(a/t)**2+(0.5-1/(0.65+a/c)+14*(1-a/c)**24)*(a/t)**4)*g*fphai*fw
        else:
            Q=1+1.464*(c/a)**1.65
            g=1
            fphai=np.sqrt(c/a)
            fw=np.sqrt(1.0/np.cos(np.pi*c/(2*b)*np.sqrt(a/t)))
            FA=(np.sqrt(c/a)*(1+0.04*c/a)+0.2*(c/a)**4*(a/t)**2-0.11*(c/a)**4*(a/t)**4)*g*fphai*fw
            H=1+(-2.11+0.77*c/a)*a/t+(0.55-0.72*(c/a)**0.75+0.14*(c/a)**1.5)*(a/t)**2
        KA=FA*(Sm+H*Sb)*np.sqrt(np.pi*a/Q)
        if a/c <=1.0:
            Q=1+1.464*(a/c)**1.65
            g=1.1+0.35*(a/t)**2
            fphai=np.sqrt(a/c)
            fw=np.sqrt(1.0/np.cos(np.pi*c/(2*b)*np.sqrt(a/t)))
            FB=(1.13-0.09*a/c+(-0.54+0.89/(0.2+a/c))*(a/t)**2+(0.5-1/(0.65+a/c)+14*(1-a/c)**24)*(a/t)**4)*g*fphai*fw
            H=1-0.34*a/t-0.11*a/c*a/t
        else:
            Q=1+1.464*(c/a)**1.65
            g=1.1+0.35*c/a*(a/t)**2
            fphai=1
            fw=np.sqrt(1.0/np.cos(np.pi*c/(2*b)*np.sqrt(a/t)))
            FB=(np.sqrt(c/a)*(1+0.04*c/a)+0.2*(c/a)**4*(a/t)**2-0.11*(c/a)**4*(a/t)**4)*g*fphai*fw
            H=1+(-0.04-0.41*c/a)*a/t+(0.55-1.93*(c/a)**0.75+1.38*(c/a)**1.5)*(a/t)**2
        KB=FB*(Sm+H*Sb)*np.sqrt(np.pi*a/Q)
        res={
            'KA':KA,
            'KB':KB
        }
        super().SetRes(res)
class K_1_a_2(Base):
    #by S.Sakai
    def __init__(self):
        super
        super().SetTitle('半楕円表面き裂 ASME Section XI, Appendix A の解')

        super().SetRefer(
            "ASME Boiler and Pressure Vessel Code, Section XI, Rules for Inservice Inspection of Nuclear Power Plant Components, 2004\n"
            "Cipolla, R. C.: Technical Basis for the Residual Stress Intensity Factor Equation for Surface Flaws in ASME Section XI Appendix A, ASME PVP, Vol. 313-1, p. 105, 1995"
        )

        # Applicable range: 0 < a/t ≤ 0.8, 0 < a/c ≤ 1 

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        c = df['c']          # half surface length
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigmaY = df['Sy']

        data = dm.Finput('K-1-a-2.csv')
        target_point = np.array([[a / t, a / c]])

        FA = np.zeros(4, dtype=float)           # F0A..F3A
        for ith in range(1, 5):                 # 1,2,3,4  (→ F0A..F3A)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(4, dtype=float)           # F0B..F3B
        for ith in range(5, 9):                 # 5,6,7,8  (→ F0B..F3B)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 5] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3
        qyA = (SA**2) / (6.0 * sigmaY**2)
        QA = 1.0 + 1.464 * (a / c)**1.65 - qyA
        KA = SA * np.sqrt(np.pi * a / QA)

        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3
        qyB = (SB**2) / (6.0 * sigmaY**2)
        QB = 1.0 + 1.464 * (a / c)**1.65 - qyB
        KB = SB * np.sqrt(np.pi * a / QB)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_1_a_3(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['a','c','t','sigma0','sigma1','sigma2','sigma3'])
        super().SetTitle('半楕円表面き裂 白鳥の解')

        super().SetRefer(
            "白鳥: 影響関数法による応力拡大係数の解析, 日本機械学会講習会教材, 表面き裂—その解析と評価—, No.900-2, p. 1, 1990"
        )

        # Applicable range: 0.1 ≤ a/t ≤ 0.8, 0.2 ≤ a/c ≤ 2

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        c = df['c']          # half surface length
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        # sigma0, sigma1, sigma2, sigma3 は、き裂深さ方向の応力分布
        #   σ = σ0 + σ1·ξ + σ2·ξ² + σ3·ξ³
        # における多項式展開の係数を表す
        # ここで ξ = 1 - u/a （u：表面からの距離，a：き裂深さ）
        data = dm.Finput('K-1-a-3.csv')
        target_point = np.array([[a / t, a / c]])

        FA = np.zeros(4, dtype=float)           # F0A..F3A
        for ith in range(1, 5):                 # 1,2,3,4  (→ F0A..F3A)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(4, dtype=float)           # F0B..F3B
        for ith in range(5, 9):                 # 5,6,7,8  (→ F0B..F3B)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 5] = float(Fi)

        Q = 1.0 + 1.464 * (a / c)**1.65

        # 最深点の応力拡大係数
        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3
        KA = SA * np.sqrt(np.pi * a / Q)

        # 表面点の応力拡大係数
        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3
        KB = SB * np.sqrt(np.pi * a / Q)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_1_b_1(Base):
    def __init__(self):
        super().SetInputItems(['a','t','b','P','M'])
        super().SetTitle('長い表面き裂(片側) Tada らの解')
        super().SetRefer('Tada, H., Paris, P. C.,and Irwin, G. R.: The Stress Analysis of Cracks Handbook, Third edition, ASME, 2000')

        # Applicable range: 0 < a/t < 1 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # axial load
        M = df['M']          # bending moment

        sigma_m = P / (2.0 * b * t) 
        sigma_b = 3.0 * M / (b * t**2)
        theta = np.pi * a / (2.0 * t)
        root_term = np.sqrt((2.0 * t) / (np.pi * a) * np.tan(theta))
        cos_term = np.cos(theta)
        Fm = root_term * (0.752 + 2.02 * (a / t) + 0.37 * (1.0 - np.sin(theta))**3) / cos_term
        Fb = root_term * (0.923 + 0.199 * (1.0 - np.sin(theta))**4) / cos_term

        K = (Fm * sigma_m + Fb * sigma_b) * np.sqrt(np.pi * a)

        res = {'K': K}
        super().SetRes(res)
class K_1_c_1(Base):
    def __init__(self):
        super
        super().SetTitle('長い表面き裂(両側) Tada らの解')
        super().SetRefer('Tada, H., Paris, P. C., and Irwin, G. R.: The Stress Analysis of Cracks Handbook, Third edition, ASME, 2000')

        # Applicable range: 0 < a/t < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # axial load

        sigma_m = P / (2.0 * b * t)
        theta = np.pi * a / t
        Fm = (1.0 + 0.122 * np.cos(theta)**4) * np.sqrt((t / (np.pi * a)) * np.tan(theta))
        
        K = Fm * sigma_m * np.sqrt(np.pi * a)

        res = {'K': K}
        super().SetRes(res)

class K_1_d_1(Base):
    def __init__(self):
        super().SetInputItems(['c','t','b','P','M'])
        super().SetTitle('中央貫通き裂 Shih らの解（き裂が短い場合）')
        super().SetRefer('Shih, G. C., Paris, P. C., and Erdogan, F.: Stress Intensity Factors for Plane Extension and Plate Bending Problems, Trans. ASME, J. of Applied Mechanics, 29, p. 306, 1962')

        # Applicable range: 0 < c/b ≤ 0.15

    def Calc(self):
        df = super().GetData()

        c = df['c']          # crack half-length
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # axial load
        M = df['M']          # bending moment

        sigma_m = P/(2.0*b*t)
        sigma_b = 3.0*M/(b*t**2)

        #開口側の応力拡大係数

        FmA, FbA = 1.0, 1.0

        KA = (FmA*sigma_m + FbA*sigma_b)*np.sqrt(np.pi*c)

        #閉口側の応力拡大係数

        FmB, FbB = 1.0, -1.0
        
        KB = (FmB*sigma_m + FbB*sigma_b)*np.sqrt(np.pi*c)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)

class K_1_d_2(Base):
    def __init__(self):
        super().SetInputItems(['c','t','b','P','M'])
        super().SetTitle('中央貫通き裂 Tada らの解（き裂が長い場合）')
        super().SetRefer('Tada, H., Paris, P. C., and Irwin, G. R.: The Stress Analysis of Cracks Handbook, Third edition, ASME, 2000')

        # Applicable range: 0 < c/b < 1

    def Calc(self):
        df = super().GetData()

        c = df['c']          # crack half-length
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # axial load
        #M = df['M']          # bending moment

        sigma_m = P/(2.0*b*t)
        ratio = c/b
        theta = np.pi*c/(2.0*b)
        Fm = (1.0 - 0.025*ratio**2 + 0.06*ratio**4) / np.sqrt(np.cos(theta))
        
        K = Fm * sigma_m * np.sqrt(np.pi*c)

        res = {'K': K}
        super().SetRes(res)
class K_1_e_1(Base):
    def __init__(self):
        super().SetInputItems(['a','c','t','b','e','P','M'])
        super().SetTitle('楕円内部き裂 Ovchinnikov–Vasiltchenko の解')
        super().SetRefer("Ovchinnikov, A. V., and Vasiltchenko, G. S.: The Defect Schematization and SIF Determination for Assessment of the Vessel and Piping Integrity, Final Report, CHIITMASH Project 125-01-90, p. 1, 1990")

        # Applicable range: 0 < a/t ≤ 0.45(1 - 2e/t), 0 < a/c ≤ 1, 0 ≤ e/t ≤ 0.5, 0 < c/b ≤ 0.15

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth (semi-minor)
        c = df['c']          # crack half-length (semi-major)
        t = df['t']          # thickness
        b = df['b']          # half width
        e = df['e']          # offset from mid-plane
        P = df['P']          # axial load
        M = df['M']          # bending moment

        sigma_m = P/(2.0*b*t)
        sigma_b = 3.0*M/(b*t**2)

        ac = a/c
        at = a/t
        et = e/t
        L = (2.0*at)/(1.0 - 2.0*et)

        #評価点Aにおける応力拡大係数

        denom_A = (1.0 - (L**1.8)*(1.0 - 0.4*ac - et**2))**0.54
        FmA = (1.01 - 0.37*ac)/denom_A
        FbA = (1.01 - 0.37*ac)*(2.0*et + at + 0.34*ac*at)/denom_A

        KA = (FmA*sigma_m + FbA*sigma_b)*np.sqrt(np.pi*a)

        #評価点Bにおける応力拡大係数

        denom_B = (1.0 - (L**1.8)*(1.0 - 0.4*ac - 0.8*et**2))**0.54
        FmB = (1.01 - 0.37*ac)/denom_B
        FbB = (1.01 - 0.37*ac)*(2.0*et + at + 0.34*ac*at)/denom_B

        KB = (FmB*sigma_m + FbB*sigma_b)*np.sqrt(np.pi*a)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)
class K_1_e_2(Base):
    def __init__(self):
        super().SetInputItems(['a','b','c','t','e','P','M','Sy'])
        super().SetTitle('楕円内部き裂 ASME Section XI, Appendix A の解')

        super().SetRefer(
            "ASME Boiler and Pressure Vessel Code, Section XI, Rules for Inservice Inspection of Nuclear Power Plant Components, 2004"
        )

        # Applicable range: 0.075 < a/t ≤ 0.325, 0 ≤ e/t ≤ 0.35

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack half-depth (semi-minor axis)
        b = df['b']          # plate half-width
        c = df['c']          # crack half-length (semi-major axis)
        t = df['t']          # thickness
        e = df['e']          # offset from mid-thickness
        P = df['P']          # axial force 
        M = df['M']          # bending moment
        Sy = df['Sy']        # yield strength

        sigma_m = P / (2.0 * b * t)
        sigma_b = 3.0 * M / (b * t**2)

        data = dm.Finput('K-1-e-2.csv')
        target_point = np.array([[a / t, e / t]])

        # 1 -> FmA, 2 -> FmB, 3 -> FbA, 4 -> FbB
        X1, W1 = dm.CSV2XW(data, 1)
        r2_score = dm.KrigCalc(X1, W1)
        FmA, _sigma = dm.Eval(target_point)
        FmA = float(FmA)

        X2, W2 = dm.CSV2XW(data, 2)
        r2_score = dm.KrigCalc(X2, W2)
        FmB, _sigma = dm.Eval(target_point)
        FmB = float(FmB)
        
        X3, W3 = dm.CSV2XW(data, 3)
        r2_score = dm.KrigCalc(X3, W3)
        FbA, _sigma = dm.Eval(target_point)
        FbA = float(FbA)
        
        X4, W4 = dm.CSV2XW(data, 4)
        r2_score = dm.KrigCalc(X4, W4)
        FbB, _sigma = dm.Eval(target_point)
        FbB = float(FbB)

        # 評価点Aにおける応力拡大係数
        SA = FmA * sigma_m + FbA * sigma_b
        qyA = (SA**2) / (6.0 * Sy**2)
        QA = 1.0 + 1.464 * (a / c)**1.65 - qyA
        KA = SA * np.sqrt(np.pi * a / QA)

        # 評価点Bにおける応力拡大係数
        SB = FmB * sigma_m + FbB * sigma_b
        qyB = (SB**2) / (6.0 * Sy**2)
        QB = 1.0 + 1.464 * (a / c)**1.65 - qyB
        KB = SB * np.sqrt(np.pi * a / QB)

        super().SetRes({'KA': KA, 'KB': KB})
class K_1_e_3(Base):
    def __init__(self):
        super().SetInputItems(['a','c','t','b','P'])
        super().SetTitle('楕円内部き裂 Raju–Newman の解')
        super().SetRefer('Newman, J. C. Jr., and Raju, I. S.: Stress-Intensity Factor Equations for Cracks in Three-Dimensional Finite Bodies, NASA Technical Memorandum 83200, NASA, 1981')

        # Applicable range: c/b < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack semi-minor (depth)
        c = df['c']          # crack semi-major (half-length)
        t = df['t']          # thickness
        b = df['b']          # half width
        P = df['P']          # axial load

        sigma_m = P/(2.0*b*t)

        ac = a/c
        at = a/t
        theta_w = (np.pi*c/(2.0*b))*np.sqrt(at)
        f_w = (1.0/np.cos(theta_w))**0.5

        if ac <= 1.0:
            Q = 1.0 + 1.464*(ac**1.65)
            base = 1.0 + (0.05/(0.11 + ac**1.5))*(at**2) + (0.29/(0.23 + ac**1.5))*(at**4)
            # Point A
            gA = 1.0
            fphiA = 1.0
            FA = base*gA*fphiA*f_w
            # Point C
            gC = 1.0 - (at**4)/(1.0 + 4.0*(ac))
            fphiC = np.sqrt(ac)
            FC = base*gC*fphiC*f_w
        else:
            Q = 1.0 + 1.464*((c/a)**1.65)
            base = np.sqrt(c/a) + (0.05/(0.11 + ac**1.5))*(at**2) + (0.29/(0.23 + ac**1.5))*(at**4)
            # Point A
            gA = 1.0
            fphiA = np.sqrt(c/a)
            FA = base*gA*fphiA*f_w
            # Point C
            gC = 1.0 - (at**4)/(1.0 + 4.0*(ac))
            fphiC = 1.0
            FC = base*gC*fphiC*f_w

        #評価点Aにおける応力拡大係数

        KA = FA*sigma_m*np.sqrt(np.pi*a/Q)

        #評価点Cにおける応力拡大係数

        KC = FC*sigma_m*np.sqrt(np.pi*a/Q)

        res = {'KA': KA, 'KC': KC}
        super().SetRes(res)

class K_2_a_1(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','sigma0','sigma1','sigma2','sigma3'])
        super().SetTitle('軸方向内表面半楕円表面き裂　Fett らの解')

        super().SetRefer(
            "Fett, T., Munz, D., and Neuman, J.: Local Stress Intensity Factors for Surface Cracks in Plates under Power-Shaped Stress Distributions, Engineering Fracture Mechanics, 36, 4, p. 647, 1990\n"
            "Raju, I. S. and Newman, J. C.: Stress Intensity Factor Influence Coefficients for Internal and External Surface Cracks in Cylindrical Vessels, ASME PVP, 58, p. 37, 1978"
        )

        # Applicable range: 0 < a/t ≤ 0.8, 0.2 ≤ a/c ≤ 1, 4 ≤ Ri/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface length
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        dataA=[]
        dataA.append(dm.Finput('K-2-a-1-F0A.csv'))
        dataA.append(dm.Finput('K-2-a-1-F1A.csv'))
        dataA.append(dm.Finput('K-2-a-1-F2A.csv'))
        dataA.append(dm.Finput('K-2-a-1-F3A.csv'))
        dataB=[]
        dataB.append(dm.Finput('K-2-a-1-F0B.csv'))
        dataB.append(dm.Finput('K-2-a-1-F1B.csv'))
        dataB.append(dm.Finput('K-2-a-1-F2B.csv'))
        dataB.append(dm.Finput('K-2-a-1-F3B.csv'))
        target_point = np.array([[a / t, a / c, Ri / t]])
        z=[4.0,10.0] #added by S.Sakai
        FA = np.zeros(4, dtype=float)           # F0A..F3A
        for ith in range(1, 5):                 # 1,2,3,4  (→ F0A..F3A)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(4, dtype=float)           # F0B..F3B
        for ith in range(5, 9):                 # 5,6,7,8  (→ F0B..F3B)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-5],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 5] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3
        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3

        # 最深点の応力拡大係数
        KA = SA * np.sqrt(np.pi * a)

        # 表面点の応力拡大係数
        KB = SB * np.sqrt(np.pi * a)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_2_a_2(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','sigma0','sigma1','sigma2','sigma3'])
        super().SetTitle('軸方向内表面半楕円表面き裂　白鳥の解')

        super().SetRefer(
            "白鳥: 影響関数法による応力拡大係数の解析, 日本機械学会講習会教材, 表面き裂—その解析と評価—, No.900-2, p. 1, 1990"
        )

        # Applicable range: 0.1 ≤ a/t ≤ 0.8, 0.2 ≤ a/c ≤ 1, 1/9 ≤ Ri/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']

        #data = dm.Finput('K-2-a-2.csv')
        dataA=[]
        dataA.append(dm.Finput('K-2-a-2-F0A.csv'))
        dataA.append(dm.Finput('K-2-a-2-F1A.csv'))
        dataA.append(dm.Finput('K-2-a-2-F2A.csv'))
        dataA.append(dm.Finput('K-2-a-2-F3A.csv'))
        dataB=[]
        dataB.append(dm.Finput('K-2-a-2-F0B.csv'))
        dataB.append(dm.Finput('K-2-a-2-F1B.csv'))
        dataB.append(dm.Finput('K-2-a-2-F2B.csv'))
        dataB.append(dm.Finput('K-2-a-2-F3B.csv'))
        target_point = np.array([[a / t, a / c, Ri / t]])
        z=[1./9.,10.0] #added by S.Sakai
        FA = np.zeros(4, dtype=float)           # F0A..F3A
        for ith in range(1, 5):                 # 1,2,3,4  (→ F0A..F3A)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(4, dtype=float)           # F0B..F3B
        for ith in range(5, 9):                 # 5,6,7,8  (→ F0B..F3B)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-5],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 5] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3
        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3

        Q = 1.0 + 1.464 * (a / c)**1.65

        # 最深点の応力拡大係数
        KA = SA * np.sqrt(np.pi * a / Q)

        # 表面点の応力拡大係数
        KB = SB * np.sqrt(np.pi * a / Q)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)

class K_2_a_3(Base):
    # by S.Sakai
    def __init__(self):
        super().SetInputItems(['Ro','Ri','p','a','c','t'])
        super().SetTitle('軸方向無い表面半楕円表面亀裂，Zahoorの解')
        super().SetRefer('Zahoor,A.:Ductile Fracture Handbook Volume 3,EPRI NP-6301-D,1991')
    def Calc(self):
        df=super().GetData()
        Ro=df['Ro']
        Ri=df['Ri']
        p=df['p']
        Sm=(Ro*Ro+Ri*Ri)/(Ro*Ro-Ri*Ri)*p
        a=df['a']
        c=df['c']
        t=df['t']
        ar=(a/t)/(a/c)**0.58
        FA=0.25+(0.4759*ar+0.1262*ar*ar)/(0.102*(Ri/t)-0.02)**0.1
        KA=FA*Sm*np.sqrt(np.pi*t)
        FB=FA*(1.06+0.28*(a/t)**2)*(a/c)**0.41
        KB=FB*Sm*np.sqrt(np.pi*t)
        res={'KA':KA,
             'KB':KB}
        super().SetRes(res)
class K_2_a_3(Base):
    def __init__(self):
        super().SetInputItems(['Ro','Ri','p','a','c','t'])
        super().SetTitle('軸方向内表面半楕円表面き裂 Zahoor の解')
        super().SetRefer('Zahoor, A.: Ductile Fracture Handbook Volume 3, EPRI NP-6301-D, 1991')

        # Applicable range: 0.05 ≤ a/t ≤ 0.85, 0.1 ≤ a/c ≤ 1, 0.2 ≤ α, 1 ≤ Ri/t ≤ 10

    def Calc(self):
        df = super().GetData()

        a  = df['a']          # crack depth
        c  = df['c']          # half surface crack length
        t  = df['t']          # wall thickness
        Ri = df['Ri']         # inner radius
        Ro = df['Ro']         # outer radius
        p  = df['p']          # internal pressure

        sigma_m = ((Ro**2 + Ri**2) / (Ro**2 - Ri**2)) * p
        alpha   = (a/t) / ((a/c)**0.58)

        # 最深点の応力拡大係数
        denomA = (0.102*(Ri/t) - 0.02)**0.1
        FA = 0.25 + (0.4759*alpha + 0.1262*alpha**2) / denomA
        KA = FA * sigma_m * np.sqrt(np.pi * t)

        # 表面点の応力拡大係数
        FB = FA * (1.06 + 0.28*(a/t)**2) * (a/c)**0.41
        KB = FB * sigma_m * np.sqrt(np.pi * t)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)
class K_2_b_1(Base):
    def __init__(self):
        super().SetInputItems(['a','t','Ri','sigma0','sigma1','sigma2','sigma3','sigma4'])
        super().SetTitle('軸方向内表面長い表面き裂 Fuhley-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service, "
            "API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ Ri/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-2-b-1.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        # 応力拡大係数
        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)

class K_2_b_2(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['Ro','Ri','p','a'])
        super().SetTitle('軸方向内表面長い表面亀裂，Zahoorの解')
        super().SetRefer('Zahoor,A.:Closed Form Expressions for Fracture Mechanics Analysis of Cracked Pipes, Trans.ASME, J. of Pressure Vessel Technology,107,p.203,1987')
    def Calc(self):
        df=super().GetData()
        Ro=df['Ro']
        Ri=df['Ri']
        p=df['p']
        Sm=2*Ro*Ro/(Ro*Ro-Ri*Ri)*p
        a=df['a']
        t=Ro-Ri
        if Ri/t >=5.0 and Ri/t<10.0:
            A=(0.125*(Ri/t)-0.25)**0.25
        if Ri/t >=10.0 and Ri/t<=20.0:
            A=(0.2*(Ri/t)-1)**0.25
        F=1.1+A*(4.951*(a/t)**2+1.092*(a/t)**4)
        K=F*Sm*np.sqrt(np.pi*a)
        res={'K':K}
        super().SetRes(res)
class K_2_c_1(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','sigma0','sigma1','sigma2','sigma3'])
        super().SetTitle('軸方向外表面半楕円表面き裂　Fett らの解')

        super().SetRefer(
            "Fett, T., Munz, D., and Neuman, J.: Local Stress Intensity Factors for Surface Cracks in Plates under Power-Shaped Stress Distributions, Engineering Fracture Mechanics, 36, 4, p. 647, 1990\n"
            "Raju, I. S. and Newman, J. C.: Stress Intensity Factor Influence Coefficients for Internal and External Surface Cracks in Cylindrical Vessels, ASME PVP, 58, p. 37, 1978"
        )

        # Applicable range: 0 < a/t ≤ 0.8, 0.2 ≤ a/c ≤ 1, 4 ≤ Ri/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']

        #data = dm.Finput('K-2-c-1.csv')
        dataA=[]
        dataA.append(dm.Finput('K-2-c-1-F0A.csv'))
        dataA.append(dm.Finput('K-2-c-1-F1A.csv'))
        dataA.append(dm.Finput('K-2-c-1-F2A.csv'))
        dataA.append(dm.Finput('K-2-c-1-F3A.csv'))
        dataB=[]
        dataB.append(dm.Finput('K-2-c-1-F0B.csv'))
        dataB.append(dm.Finput('K-2-c-1-F1B.csv'))
        dataB.append(dm.Finput('K-2-c-1-F2B.csv'))
        dataB.append(dm.Finput('K-2-c-1-F3B.csv'))
        target_point = np.array([[a / t, a / c, Ri / t]])
        z=[4.0,10.0] #added by S.Sakai
        FA = np.zeros(4, dtype=float)           # F0A..F3A
        for ith in range(1, 5):                 # 1,2,3,4  (→ F0A..F3A)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(4, dtype=float)           # F0B..F3B
        for ith in range(5, 9):                 # 5,6,7,8  (→ F0B..F3B)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-5],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 5] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3
        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3

        # 最深点の応力拡大係数
        KA = SA * np.sqrt(np.pi * a)

        # 表面点の応力拡大係数
        KB = SB * np.sqrt(np.pi * a)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_2_c_2(Base):
    def __init__(self):
        super().SetInputItems(['Ro','Ri','p','a','c','t'])
        super().SetTitle('軸方向外表面半楕円表面き裂 Zahoor の解')
        super().SetRefer('Zahoor, A.: Ductile Fracture Handbook Volume 3, EPRI NP-6301-D, 1991')

        # Applicable range: 0.05 ≤ a/t ≤ 0.85, 0.1 ≤ a/c ≤ 1, 0.2 ≤ α, 2 ≤ Ri/t ≤ 10

    def Calc(self):
        df = super().GetData()

        a  = df['a']    # crack depth
        c  = df['c']    #half surface crack length
        t  = df['t']    # wall thickness
        Ri = df['Ri']   # inner radius
        Ro = df['Ro']   # outer radius
        p  = df['p']    # internal pressure

        # 最深点の応力拡大係数
        sigma_m = (2.0 * Ri**2 / (Ro**2 - Ri**2)) * p
        alpha = (a/t) / ((a/c)**0.58)
        denomA = (0.11*(Ri/t) - 0.1)**0.1
        FA = 0.25 + (0.42*alpha + 0.21*alpha**2) / denomA
        KA = FA * sigma_m * np.sqrt(np.pi * t)

        # 表面点の応力拡大係数
        FB = FA * (1.0 + 0.33*(a/t)**2) * (a/c)**0.47
        KB = FB * sigma_m * np.sqrt(np.pi * t)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)
class K_2_d(Base):
    def __init__(self):
        super().SetInputItems(['a','t','Ri','sigma0','sigma1','sigma2','sigma3','sigma4'])
        super().SetTitle('軸方向外表面長い表面き裂 Fuhley-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service, "
            "API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ Ri/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-2-d.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)
class K_2_e_1(Base):
    def __init__(self):
        super().SetInputItems(['c','t','Ri','sigma_m','sigma_b'])
        super().SetTitle('軸方向貫通き裂　Erdogan-Kibler の解')

        super().SetRefer(
            "Erdogan, F., and Kibler, J. J.: Cylindrical and Spherical Shells with Cracks, International Journal of Fracture Mechanics, 5, p. 229, 1969"
        )

        # Applicable range: 0 < c/t ≤ 12.5, 10 ≤ Ri/t ≤ 20

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma_m = df['sigma_m']
        sigma_b = df['sigma_b']

        data = dm.Finput('K-2-e-1.csv')
        target_point = np.array([[c / t, Ri / t]])

        FA = np.zeros(2, dtype=float)           # FmA, FbA
        for ith in range(1, 3):                 # 1,2  (→ FmA, FbA)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(2, dtype=float)           # FmB, FbB
        for ith in range(3, 5):                 # 3,4  (→ FmB, FbB)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 3] = float(Fi)

        # 内表面における応力拡大係数
        KA = (FA[0]*sigma_m + FA[1]*sigma_b) * np.sqrt(np.pi * c)

        # 外表面における応力拡大係数
        KB = (FB[0]*sigma_m + FB[1]*sigma_b) * np.sqrt(np.pi * c)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)

class K_2_e_2(Base):
    #by S.Sakai
    def __init__(self):
        super().SetInputItems(['p','R','t','c'])
        super().SetTitle('軸方向貫通亀裂，ASME Code Case N-513の解')
        super().SetRefer('ASME Boiler and Pressure Vessel Code, Code Case N-513, Evaluation Criteria for Temporary Acceptance of Flaws in Calss 3 Piping, 1997')
    def Calc(self):
        df=super().GetData()
        p=df['p']
        R=df['R']
        t=df['t']
        Sm=p*R/t
        c=df['c']
        l=c/np.sqrt(R*t)
        F=1+0.072449*l+0.64856*l*l-0.2327*l*l*l+0.038154*l**4-0.0023487*l**5
        K=F*Sm*np.sqrt(np.pi*c)
        res={'K':K}
        super().SetRes(res)
class K_2_e_3(Base):
    def __init__(self):
        super().SetInputItems(['c','t','Ri','sigma0','sigma1','sigma2','sigma3','sigma4'])
        super().SetTitle('軸方向貫通き裂　Zang の解')

        super().SetRefer(
            "Zang, W.: Stress Intensity Factor Solutions for Axial and Circumferential Through-Wall Cracks in Cylinders, "
            "SINTAP/SAQ/02, SAQ Control AB, 1997"
        )

        # Applicable range: 0.5 ≤ c/t ≤ 25, 5 ≤ Ri/t ≤ 100

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-2-e-3.csv')
        target_point = np.array([[c / t, Ri / t]])

        FA = np.zeros(5, dtype=float)           # F0A..F4A
        for ith in range(1, 6):                 # 1..5 -> F0A..F4A
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(5, dtype=float)           # F0B..F4B
        for ith in range(6, 11):                # 6..10 -> F0B..F4B
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 6] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 + FA[3]*sigma3 + FA[4]*sigma4
        SB = FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 + FB[3]*sigma3 + FB[4]*sigma4

        # 内表面における応力拡大係数
        KA = SA * np.sqrt(np.pi * c)

        # 外表面における応力拡大係数
        KB = SB * np.sqrt(np.pi * c)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_2_f_1(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','sigma0','sigma1','sigma2','sigma3','sigma_bg'])
        super().SetTitle('周方向内表面半楕円表面き裂　Chapuliot らの解')
        super().SetRefer(
            "Chapuliot, S.: Formulaire de KI Pour les Tubes Comportant un Defaut de Surface Semi-elliptique "
            "Longitudinal ou Circonférentiel, interne ou externe, Rapport CEA-R-5900, 2000"
        )
        # Applicable range: 0 < a/t ≤ 0.8, 0 < a/c ≤ 1, 1 ≤ Ri/t < ∞

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-f-1.csv')
        target_point = np.array([[ a / t,Ri / t, a / c]])
        dataA=[]
        for ii in range(1,6):
            dd=[]
            for i in range(6):
                j=ii+i*10
                dd+=dm.extract_block(data,j)
            dataA.append(dd)
        dataB=[]
        for ii in range(1,6):
            dd=[]
            for i in range(5):
                j=ii+i*10+5
                dd+=dm.extract_block(data,j)
            dataB.append(dd)
        zA=[1.,1./2.,1./4.,1./8.,1./16.,0.0]
        zB=[1.,1./2.,1./4.,1./8.,1./16.]
        FA = np.zeros(5, dtype=float)
        for ith in range(1, 5 + 1):
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],zA) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(5, dtype=float)
        for ith in range(6, 10 + 1):
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-6],zB) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 6] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1*(a/t) + FA[2]*sigma2*(a/t)**2 + FA[3]*sigma3*(a/t)**3 + FA[4]*sigma_bg
        SB = FB[0]*sigma0 + FB[1]*sigma1*(a/t) + FB[2]*sigma2*(a/t)**2 + FB[3]*sigma3*(a/t)**3 + FB[4]*sigma_bg

        # 最深点の応力拡大係数
        KA = SA * np.sqrt(np.pi * a)

        # 表面点の応力拡大係数
        KB = SB * np.sqrt(np.pi * a)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)
class K_2_f_2(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','sigma_m','sigma_bg'])
        super().SetTitle('周方向内表面半楕円表面き裂 白鳥の解')

        super().SetRefer(
            "白鳥: 影響関数法による応力拡大係数の解析, 日本機械学会講習会教材, "
            "表面き裂―その解析と評価―, No. 900-2, p. 1, 1990"
        )

        # Applicable range: 0.1 ≤ a/t ≤ 0.8, 0.2 ≤ a/c ≤ 1, 1.25 ≤ Ri/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        sigma_m  = df['sigma_m']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-f-2.csv')
        target_point = np.array([[a / t, a / c, Ri / t]])
        z=[1.25,5./3.,2.5,5.,10.]
        dataA=[]
        for ii in range(1,3):
            dd=[]
            for i in range(len(z)+1):
                j=ii+i*4
                dd+=dm.extract_block(data,j)
            dataA.append(dd)
        dataB=[]
        for ii in range(1,3):
            dd=[]
            for i in range(len(z)+1):
                j=ii+i*4+2
                dd+=dm.extract_block(data,j)
            dataB.append(dd)
        FA = np.zeros(2, dtype=float)           # FmA, FbgA
        for ith in range(1, 3):                 # 1,2 (→ FmA, FbgA)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(2, dtype=float)           # FmB, FbgB
        for ith in range(3, 5):                 # 3,4 (→ FmB, FbgB)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-3],z) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 3] = float(Fi)

        Q = 1.0 + 1.464 * (a / c)**1.65

        # 最深点の応力拡大係数
        SA = FA[0]*sigma_m + FA[1]*sigma_bg
        KA = SA * np.sqrt(np.pi * a / Q)

        # 表面点の応力拡大係数
        SB = FB[0]*sigma_m + FB[1]*sigma_bg
        KB = SB * np.sqrt(np.pi * a / Q)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)
class K_2_f_3(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','P','M'])
        super().SetTitle('周方向内表面半楕円表面き裂 Zahoor の解')

        super().SetRefer(
            "Zahoor, A.: Closed Form Expressions for Fracture Mechanics Analysis of Cracked Pipes, "
            "Trans. ASME, J. of Pressure Vessel Technology, 107, p. 203, 1985\n"
            "Zahoor, A.: Ductile Fracture Handbook Volume 2, EPRI NP-6301-D, 1990"
        )

        # Applicable range (軸方向荷重に対して):
        # 0.05 ≤ a/t ≤ 0.8, 1/6 ≤ a/c ≤ 2/3, 5 ≤ R/t ≤ 20
        # (曲げモーメントに対して):
        # 0.05 ≤ a/t ≤ 0.8, a/c ≤ 2/3, 5 ≤ R/t ≤ 160

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        P  = df['P']         # axial load
        M  = df['M']         # bending moment

        data = dm.Finput('K-2-f-3.csv')
        target_point = np.array([[a / t, a / c, Ri / t]])
        z=[5.0,10.0,15.0,20.0,40.0,80.0,160.0]
        dataAbg=[]
        dd=[]
        for i in range(len(z)+1):
            dd+=dm.extract_block(data,i)
        dataAbg.append(dd)
        #X_1, W_1 = dm.CSV2XW(data, 1)          # 1列目 → F_bg^A
        X_1,W_1=dm.Fconv3D(dataAbg[0],z) #modified by S.Sakai
        r2_score = dm.KrigCalc(X_1, W_1)
        FbgA, _sigma = dm.Eval(target_point)
        FbgA = float(FbgA)

        sigma_m = P/(2.0*np.pi*Ri*t)
        sigma_bg = M/(np.pi*Ri**2*t)
        Q = 1.0 + 1.464 * (a / c)**1.65
        alpha = 2.0 * c / t
        FmA = (1.0 + (0.02 + 0.0103*alpha + 0.00617*alpha**2 + 0.0035*(1.0 + 0.7*alpha)*(Ri/t - 5.0)**0.7) * Q**2) / Q**0.5
     
        # 最深点の応力拡大係数
        K = FmA*sigma_m * np.sqrt(np.pi * a) + FbgA*sigma_bg * np.sqrt(np.pi * t)

        res = {
            'K': K
        }
        super().SetRes(res)
class K_2_g(Base):
    def __init__(self):
        super().SetInputItems(['a','t','c','Ri','R','P','M'])
        super().SetTitle('周方向内表面扇形表面き裂 ASME Section XI, Appendix C の解')
        super().SetRefer('ASME Boiler and Pressure Vessel Code, Section XI, Rules for Inservice Inspection of Nuclear Power Plant Components, 2004')

        # Applicable range: 0.08 ≤ a/t ≤ 0.8, 0 < a/c ≤ 1, 0.05 ≤ c/(πRi) ≤ 1

    def Calc(self):
        df = super().GetData()

        a  = df['a']   # crack depth
        c  = df['c']   # half surface crack length
        t  = df['t']   # wall thickness
        Ri = df['Ri']  # inner radius
        R  = df['R']   # mean radius
        P  = df['P']   # axial load
        M  = df['M']   # bending moment

        sigma_m = P/(2.0*np.pi*R*t)
        sigma_bg = M/(np.pi*R**2*t)

        cp = c/(np.pi*Ri)
        if 0.5 <= cp <= 1.0:
            cp = 0.5

        x = (a/t)*cp

        # 最深点の応力拡大係数
        FmA  = 1.1 + (a/t)*(0.15241 + 16.722*x**0.855 - 14.944*x)
        FbgA = 1.1 + (a/t)*(-0.09967 + 5.0057*x**0.565 - 2.8329*x)
        KA = (FmA*sigma_m + FbgA*sigma_bg)*np.sqrt(np.pi*a)

        res = {'KA': KA}
        super().SetRes(res)

class K_2_h_1(Base):
    def __init__(self):
        super().SetTitle('周方向内表面全周き裂 Fuhley-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service, "
            "API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ R/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Ri = df['Ri']        # mean radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-2-h-1.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)

class K_2_h_2(Base):
    def __init__(self):
        super().SetTitle('周方向内表面全周き裂 飯井らの解')
        super().SetRefer('飯井, 渡邉, 酒井: 厚肉円筒の熱応力下の疲労き裂進展健全性評価（第4報, 円筒の任意熱応力下の疲労き裂進展特性）, 日本機械学会講演論文集, Vol. A, No. 96-10, p. 373, 1996')
        # Applicable range: 0 < a/t ≤ 0.8, 5 ≤ R/t

    def Calc(self):
        df = super().GetData()

        a = df['a']      # crack depth
        t = df['t']      # wall thickness
        R = df['R']      # mean radius
        H = df['H']      # cylinder height
        E = df['E']
        Nu = df['Nu']
        M = df['M']      # bending moment

        sigma_b = 6.0*M/t**2

        at = a/t 

        beta = (3.0*(1.0-Nu**2)/(R**2*t**2))**0.25
        D = E*t**3/(12.0*(1.0-Nu**2))
        lambda_bf = (np.sinh(beta*H) + np.sin(beta*H)) / (beta*D*(np.cosh(beta*H) + np.cos(beta*H) - 2.0))
        delta_lambda = (np.pi*(1.125**2)/(2.0*E)) * ( (at**2)/((1.0-at)**2*(1.0+2.0*at)**2) ) * (1.0 + at*(1.0-at)*(0.44 + 0.25*at)) * (6.0/t)**2

        theta = 0.5*np.pi*at
        Fb0 = np.sqrt((2.0/np.pi)*at*np.tan(theta)) * (0.923 + 0.199*(1.0-np.sin(theta))**4) / np.cos(theta)
        Fb = Fb0/(1.0 + delta_lambda/lambda_bf)
        
        K = Fb*sigma_b*np.sqrt(np.pi*a)

        res = {'K': K}
        super().SetRes(res)

class K_2_i_1(Base):
    def __init__(self):
        super().SetTitle('周方向外表面半楕円表面き裂　Chapuliot らの解')

        super().SetRefer(
            "Chapuliot, S.: Formulaire de KI Pour les Tubes Comportant un Defaut de Surface Semi-elliptique "
            "Longitudinal ou Circonférentiel, interne ou externe, Rapport CEA-R-5900, 2000"
        )

        # Applicable range: 0 < a/t ≤ 0.8, 0 < a/c ≤ 1, 1 ≤ Ri/t < ∞

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-i-1.csv')
        # 
        target_point = np.array([[a / t,Ri / t, a / c]])
        dataA=[]
        for ii in range(1,6):
            dd=[]
            for i in range(6):
                j=ii+i*10
                dd+=dm.extract_block(data,j)
            dataA.append(dd)
        dataB=[]
        for ii in range(1,6):
            dd=[]
            for i in range(5):
                j=ii+i*10+5
                dd+=dm.extract_block(data,j)
            dataB.append(dd)
        zA=[1.,1./2.,1./4.,1./8.,1./16.,0.0]
        zB=[1.,1./2.,1./4.,1./8.,1./16.]
        FA = np.zeros(5, dtype=float)           # F0A..F3A, FbgA
        for ith in range(1, 6):                 # 1..5  (→ F0A..F3A, FbgA)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataA[ith-1],zA) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(5, dtype=float)           # F0B..F3B, FbgB
        for ith in range(6, 11):                # 6..10 (→ F0B..F3B, FbgB)
            #X_ith, W_ith = dm.CSV2XW(data, ith)
            X_ith,W_ith=dm.Fconv3D(dataB[ith-6],zB) #modified by S.Sakai
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 6] = float(Fi)

        SA = FA[0]*sigma0 + FA[1]*sigma1*a/t + FA[2]*sigma2*(a/t)**2 + FA[3]*sigma3*(a/t)**3 + FA[4]*sigma_bg
        SB = FB[0]*sigma0 + FB[1]*sigma1*a/t + FB[2]*sigma2*(a/t)**2 + FB[3]*sigma3*(a/t)**3 + FB[4]*sigma_bg

        # 最深点の応力拡大係数
        KA = SA * np.sqrt(np.pi * a)

        # 表面点の応力拡大係数
        KB = SB * np.sqrt(np.pi * a)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)

class K_2_i_2(Base):
    def __init__(self):
        super().SetTitle('周方向外表面半楕円表面き裂 白鳥の解')

        super().SetRefer(
            "白鳥: 影響関数法による応力拡大係数の解析, 日本機械学会講習会教材, "
            "表面き裂―その解析と評価―, No. 900-2, p. 1, 1990"
        )

        # Applicable range: 0.1 ≤ a/t ≤ 0.8, 0.2 ≤ a/c ≤ 1, 1.25 ≤ Ri/t ≤ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        Ri = df['Ri']          # mean radius
        sigma_m  = df['sigma_m']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-i-2.csv')
        #target_point = np.array([[a / c, a / t, Ri / t]])
        target_point = np.array([[a / t, a / c, Ri / t]])
        FmA=[]
        FbgA=[]
        FmB=[]
        FbgB=[]
        zRi_t=[1.25,5./3.,2.5,5.,10.]
        for i in range(len(zRi_t)):
            j=1+4*i
            FmA+=dm.extract_block(data,j)
        for i in range(len(zRi_t)):
            j=2+4*i
            FbgA+=dm.extract_block(data,j)
        for i in range(len(zRi_t)):
            j=3+4*i
            FmB+=dm.extract_block(data,j)
        for i in range(len(zRi_t)):
            j=4+4*i
            FbgB+=dm.extract_block(data,j)
        X,W=dm.Fconv3D(FmA,zRi_t) 
        r2_score = dm.KrigCalc(X, W)
        fmA, _sigma=dm.Eval(target_point)
        X,W=dm.Fconv3D(FbgA,zRi_t) 
        r2_score = dm.KrigCalc(X, W)
        fbgA, _sigma=dm.Eval(target_point)
        X,W=dm.Fconv3D(FmB,zRi_t) 
        r2_score = dm.KrigCalc(X, W)
        fmB, _sigma=dm.Eval(target_point)
        X,W=dm.Fconv3D(FbgB,zRi_t) 
        r2_score = dm.KrigCalc(X, W)
        fbgB, _sigma=dm.Eval(target_point)


        Q = 1.0 + 1.464 * (a / c)**1.65

        # 最深点の応力拡大係数
        SA =fmA*sigma_m + fbgA*sigma_bg
        KA = SA * np.sqrt(np.pi * a / Q)

        # 表面点の応力拡大係数
        SB = fmB*sigma_m + fbgB*sigma_bg
        KB = SB * np.sqrt(np.pi * a / Q)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)

class K_2_j(Base):
    def __init__(self):
        super().SetTitle('周方向外表面全周き裂 Fuhley-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service, "
            "API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ Ri/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-2-j.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)

class K_2_k_1(Base):
    def __init__(self):
        super().SetTitle('周方向貫通き裂 Sattari-Far の解')

        super().SetRefer(
            "Sattari-Far, I.: Stress Intensity Factors for Circumferential Through-Thickness Cracks "
            "in Cylinders Subjected to Local Bending, International Journal of Fracture, 53, p. R9, 1992\n"
            "Zahoor, A.: Closed Form Expressions for Fracture Mechanics Analysis of Cracked Pipes, "
            "Trans. ASME, J. of Pressure Vessel Technology, 107, p. 203, 1985"
        )

        # Applicable range: 0 < c/(π Ri) ≤ 0.5, 5 ≤ Ri/t ≤ 20

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma_m  = df['sigma_m']
        sigma_b  = df['sigma_b']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-k-1.csv')
        target_point = np.array([[c / (np.pi * Ri), Ri / t]])

        FA = np.zeros(3, dtype=float)           # FmA, FbA, FbgA
        for ith in range(1, 4):                 # 1,2,3 (→ FmA, FbA, FbgA)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(3, dtype=float)           # FmB, FbB, FbgB
        for ith in range(4, 7):                 # 4,5,6 (→ FmB, FbB, FbgB)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 4] = float(Fi)

        # 内表面における応力拡大係数
        SA = FA[0]*sigma_m + FA[1]*sigma_b + FA[2]*sigma_bg
        KA = SA * np.sqrt(np.pi * c)

        # 外表面における応力拡大係数
        SB = FB[0]*sigma_m + FB[1]*sigma_b + FB[2]*sigma_bg
        KB = SB * np.sqrt(np.pi * c)

        res = {
            'KA': KA, 'KB': KB
        }
        super().SetRes(res)



class K_2_k_2(Base):
    def __init__(self):
        super().SetInputItems(['R','c','P','M','t'])
        super().SetTitle('周方向貫通亀裂，ASME Code Case N-513の解')
        super().SetRefer('ASME Boiler and Pressure Vessel Code, Code Cae N-513,Evaluation Criteria for Temporary Acceptance of Flaws in Class 3 Piping,1997')
    def Calc(self):
        df=super().GetData()
        R=df['R']
        c=df['c']
        P=df['P']
        M=df['M']
        t=df['t']
        Sm=P/(2*np.pi*R*t)
        Sbg=M/(np.pi*R*R*t)
        evaluate_cubic = lambda x, c: c[0] + c[1]*x + c[2]*x**2 + c[3]*x**3
        x=R/t
        coeffs=[-2.02917,1.67763,-0.07987,0.00176]
        Am=evaluate_cubic(x,coeffs)
        coeffs=[7.09987,-4.42394,0.21036,-0.00463]
        Bm=evaluate_cubic(x,coeffs)
        coeffs=[7.79661,5.16676,-0.24577,0.00541]
        Cm=evaluate_cubic(x,coeffs)
        coeffs=[-3.26543,1.52784,-0.072698,0.0016011]
        Abg=evaluate_cubic(x,coeffs)
        coeffs=[11.36322,-3.91412,0.18619,-0.004099]
        Bbg=evaluate_cubic(x,coeffs)
        coeffs=[-3.18609,3.84763,-0.18304,0.00403]
        Cbg=evaluate_cubic(x,coeffs)
        evaluate_F = lambda x, c: c[0] + c[1]*x**1.5 + c[2]*x**2.5 + c[3]*x**3.5
        x=c/(np.pi*R)
        coeffs=[1,Am,Bm,Cm]
        Fm=evaluate_F(x,coeffs)
        coeffs=[1,Abg,Bbg,Cbg]
        Fbg=evaluate_F(x,coeffs)
        K=(Fm*Sm+Fbg*Sbg)*np.sqrt(np.pi*c)
        res={'K':K
            }
        super().SetRes(res)

class K_2_k_3(Base):
    def __init__(self):
        super().SetTitle('周方向貫通き裂 Zahoor の解')
        super().SetRefer(
            'Zahoor, A.: Closed Form Expressions for Fracture Mechanics Analysis of Cracked Pipes,\n'
            'Trans. ASME, J. of Pressure Vessel Technology, 107, p. 203, 1985'
        )
        # Applicable range (軸方向荷重および曲げモーメントに対して): 0 < c/(πR) ≤ 0.55, 5 ≤ R/t ≤ 20
        # Applicable range (内圧に対して): R/t = 10

    def Calc(self):
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        R = df['R']          # mean radius

        P = df['P']          # axial load
        M = df['M']          # bending moment
        p = df['p']          # internal pressure

        Ri = R - 0.5*t
        Ro = R + 0.5*t

        # （軸方向荷重および曲げモーメントに対して）
        sigma_m  = P / (2.0 * np.pi * R * t)
        sigma_bg = M / (np.pi * R**2 * t)

        x  = c / (np.pi * R)
        rt = R / t

        if rt <= 10.0:
            A = (0.125 * rt - 0.25) ** 0.25
        else:
            A = (0.4 * rt - 3.0) ** 0.25

        Fm  = 1.0 + A * (5.3303 * x**1.5 + 18.73  * x**4.24)
        Fbg = 1.0 + A * (4.5967 * x**1.5 + 2.6422 * x**4.24)

        K_PM = (Fm * sigma_m + Fbg * sigma_bg) * np.sqrt(np.pi * c)

        # （内圧に対して）
        sigma_m_p = (Ri**2 / (Ro**2 - Ri**2)) * p
        lambda_ = (c / (np.pi * R)) * (R / t) ** 0.5

        if lambda_ <= 2.0:
            Fm_p = 1.0 + 0.1501 * lambda_**1.5
        else:
            Fm_p = 0.8875 + 0.2625 * lambda_

        K_p = Fm_p * sigma_m_p * np.sqrt(np.pi * c)

        res = {'K_PM': K_PM, 'K_p': K_p}
        super().SetRes(res)

class K_2_k_4(Base):
    def __init__(self):
        super().SetTitle('周方向貫通き裂　Zang の解')

        super().SetRefer(
            "Zang, W.: Stress Intensity Factor Solutions for Axial and Circumferential Through-Wall Cracks in Cylinders, "
            "SINTAP/SAQ/02, SAQ Control AB, 1997"
        )

        # Applicable range: 0.03 ≤ c/(πR) ≤ 0.5, 5 ≤ Ri/t ≤ 100

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']
        sigma_bg = df['sigma_bg']

        data = dm.Finput('K-2-k-4.csv')
        # 座標系: [c/(πR), Ri/t]
        target_point = np.array([[c / (np.pi * Ri), Ri / t]])

        FA = np.zeros(6, dtype=float)           # F0A..F4A, FbgA
        for ith in range(1, 7):                 # 1..6 -> F0A..F4A, FbgA
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FA[ith - 1] = float(Fi)

        FB = np.zeros(6, dtype=float)           # F0B..F4B, FbgB
        for ith in range(7, 13):                # 7..12 -> F0B..F4B, FbgB
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            FB[ith - 7] = float(Fi)

        SA = (FA[0]*sigma0 + FA[1]*sigma1 + FA[2]*sigma2 +
              FA[3]*sigma3 + FA[4]*sigma4 + FA[5]*sigma_bg)
        SB = (FB[0]*sigma0 + FB[1]*sigma1 + FB[2]*sigma2 +
              FB[3]*sigma3 + FB[4]*sigma4 + FB[5]*sigma_bg)

        # 内表面における応力拡大係数
        KA = SA * np.sqrt(np.pi * c)

        # 外表面における応力拡大係数
        KB = SB * np.sqrt(np.pi * c)

        res = {'KA': KA, 'KB': KB}
        super().SetRes(res)

class K_2_l(Base):
    def __init__(self):
        super().SetTitle('軸方向内表面一定深さ矩形表面き裂 ASME Section XI, Appendix C の解')
        super().SetRefer(
            "ASME Boiler and Pressure Vessel Code, Section XI, Rules for Inservice Inspection of Nuclear Power Plant Components, 2004\n"
            "Zahoor, A.: Closed Form Expressions for Fracture Mechanics Analysis of Cracked Pipes, Trans. ASME, J. of Pressure Vessel Technology, 107, p. 203, 1985"
        )

        # Applicable range: 0.2 ≤ a/t ≤ 0.8, 1/6 ≤ a/c ≤ 2/3, 5 ≤ R/t ≤ 20

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half surface crack length
        t = df['t']          # wall thickness
        R = df['R']          # mean radius
        p = df['p']          # internal pressure

        # 最深点の応力拡大係数
        sigma_m = p*R/t
        Q = 1.0 + 1.464*(a/c)**1.65
        alpha = 2.0*c/t
        FA = 1.12 + 0.053*alpha + 0.0055*alpha**2 + (1.0 + 0.02*alpha + 0.0191*alpha**2)*(20.0 - R/t)/1400.0

        KA = FA*sigma_m*np.sqrt(np.pi*a/Q)

        res = {'KA': KA}
        super().SetRes(res)

class K_3_a(Base):
    def __init__(self):
        super().SetTitle('ノズルコーナー部の軸方向内表面半楕円表面き裂　白鳥の解')

        super().SetRefer(
            "寺門, 白鳥, 于: 影響関数法によるノズルコーナーき裂の応力拡大係数の解析, "
            "日本機械学会第9回計算力学講演会講演論文集, No. 96-25, p. 217, 1996"
        )

        # Applicable range:
        # 0.1 ≤ a/tm ≤ 0.8, 0.2 < a/c < 2,
        # ts/tm ≈ 2, Rim/tm ≈ 20, Ris/tm ≈ 2,
        # 1/3 ≤ ri/tm ≤ 0.5, ro/tm ≈ 10/13

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half surface crack length
        tm = df['tm']        # thickness (main vessel side)
        ri = df['ri']        # nozzle corner radius
        sigma_m = df['sigma_m']

        data = dm.Finput('K-3-a.csv')

        target_point = np.array([[a / tm, a / c, ri / tm]])
        FmA=[]
        FmBm=[]
        FmBs=[]
        zri_tm=[1./3.,0.5]
        for i in range(len(zri_tm)):
            j=1+3*i
            FmA+=dm.extract_block(data,j)
        for i in range(len(zri_tm)):
            j=2+3*i
            FmBm+=dm.extract_block(data,j)
        for i in range(len(zri_tm)):
            j=3+3*i
            FmBs+=dm.extract_block(data,j)

        X,W=dm.Fconv3D(FmA,zri_tm) 
        r2_score = dm.KrigCalc(X, W)
        fmA, _sigma=dm.Eval(target_point)
        X,W=dm.Fconv3D(FmBm,zri_tm) 
        r2_score = dm.KrigCalc(X, W)
        fmBm, _sigma=dm.Eval(target_point)
        X,W=dm.Fconv3D(FmBs,zri_tm) 
        r2_score = dm.KrigCalc(X, W)
        fmBs, _sigma=dm.Eval(target_point)


        Q = 1.0 + 1.464 * (a / c) ** 1.65

        # (最深点の応力拡大係数)
        KA = (fmA * sigma_m) * np.sqrt(np.pi * a / Q)

        # (容器側表面点の応力拡大係数)
        KBm = (fmBm * sigma_m) * np.sqrt(np.pi * a / Q)

        # (配管側表面点の応力拡大係数)
        KBs = (fmBs * sigma_m) * np.sqrt(np.pi * a / Q)

        res = {'KA': KA, 'KBm': KBm, 'KBs': KBs}
        super().SetRes(res)

class K_3_b_1(Base):
    def __init__(self):
        super().SetTitle('ノズルコーナー部の軸方向内表面1/4円表面き裂 Kobayashi らの解')

        super().SetRefer(
            "Kobayashi, A. S., Polvanich, N., Emery, A. F., and Lowe, W. J.: Corner Crack at a Nozzle, "
            "Proceedings of 3rd International Conference on Pressure Vessel Technology, Tokyo, p. 507, 1977"
            "Bergman, M., Brickstad, B., Dahlberg, L., Nilsson, F., and Sattari-Far, I.: A Procedure for Safety "
            "Assessment of Components with Cracks - Handbook, AS/FoU-Report, 91/01, The Swedish Plant Inspectorare, 1991"
        )

        # Applicable range: 0 < a/tm ≤ 0.8, 0 < a/Ris ≤ 3, Ris/Rm ≤ 0.6

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a   = df['a']         # crack size
        tm  = df['tm']        # wall thickness at nozzle corner
        Ris = df['Ris']       # inner radius at nozzle side
        Rm  = df['Rm']        # mean radius

        sigma00 = df['sigma00']
        sigma10 = df['sigma10']
        sigma01 = df['sigma01']
        sigma20 = df['sigma20']
        sigma02 = df['sigma02']
        sigma30 = df['sigma30']
        sigma03 = df['sigma03']
        krig = kr.Kriging()
        data = dm.Finput('K-3-b-1.csv')
        target_point = np.array([[a / Ris]])
        # FmA
        X,Y=dm.extract_1D(data,1)
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)
        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        fmA=y_krig[0] #予測値
        # FmBm
        X,Y=dm.extract_1D(data,2)
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)
        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        fmBm=y_krig[0] #予測値
        # FmBs
        X,Y=dm.extract_1D(data,3)
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)
        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        fmBs=y_krig[0] #予測値


        # 最深点の応力拡大係数
        SA = (1.08*sigma00 + 1.00*sigma10 + 1.00*sigma01 +
              0.77*sigma20 + 0.77*sigma02 + 0.50*sigma30 + 0.50*sigma03)
        KA = fmA * SA * np.sqrt(np.pi * a)

        # 容器側表面点の応力拡大係数
        SBm = (1.40*sigma00 + 0.98*sigma10 + 0.98*sigma01 +
               0.65*sigma20 + 0.80*sigma02 + 0.55*sigma30 + 0.58*sigma03)
        KBm = fmBm * SBm * np.sqrt(np.pi * a)

        # 配管側表面点の応力拡大係数
        SBs = (1.40*sigma00 + 0.98*sigma10 + 0.98*sigma01 +
               0.80*sigma20 + 0.65*sigma02 + 0.58*sigma30 + 0.55*sigma03)
        KBs = fmBs * SBs * np.sqrt(np.pi * a)

        res = {'KA': KA, 'KBm': KBm, 'KBs': KBs}
        super().SetRes(res)

class K_3_b_2(Base):
    def __init__(self):
        super().SetTitle('ノズルコーナー部の軸方向内表面1/4円表面き裂 Fife らの解')
        super().SetRefer(
            "Fife, A. B., Kobsa, I. R., Riccardella, P. C., and Watanabe, H. T.: Boiling Water Reactor Feedwater\n"
            "Nozzle/Spranger Interim Program Report, NEDO-21480, 77NED125, Class 1, General Electric, San Jose, 1977"
        )

        # Applicable range: 0 ≤ a/tm ≤ 0.5, 0 ≤ a/ts ≤ 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']

        # 最深点の応力拡大係数
        SA = 0.706*sigma0 + 0.527*(2.0*a/np.pi)*sigma1 + 0.488*((a**2)/2.0)*sigma2 + 0.393*((4.0*a**3)/(3.0*np.pi))*sigma3
        KA = SA * np.sqrt(np.pi * a)

        res = {'KA': KA}
        super().SetRes(res)

class K_3_c(Base):
    def __init__(self):
        super().SetTitle('周方向内表面全周表面き裂 配管継ぎ目付近 Buchalet-Bamford の解')

        super().SetRefer(
            "Buchalet, C. B., and Bamford, W. H.: Stress Intensity Factor Solutions for Continues Surface Flaws "
            "in Reactor Pressure Vessels, ASTM STP 590, p. 385, 1976"
        )

        # Applicable range: 0 < a/t ≤ 0.8, Ri/t ≈ 6

    def Calc(self):
        ddf={
            'A':{
                'a_t':[0,0.2,0.4,0.6,0.8],
                'data':[[1.102,1.221,1.410,1.805,2.250],
                [1.000,1.076,1.185,1.439,1.784],
                [1.000 ,1.036 ,1.085 ,1.239 ,1.514],
                [1.000 ,1.006 ,1.035 ,1.149 ,1.353]]
            },
            'B':{
                'a_t':[0,0.2,0.4,0.6,0.8],
                'data':[[1.120 ,1.172 ,1.269 ,1.481 ,1.723 ,],
                [1.000 ,1.077 ,1.164 ,1.331 ,1.533],
                [1.000 ,1.037 ,1.099 ,1.241 ,1.393],
                [1.000 ,1.022 ,1.049 ,1.156 ,1.283]]
            },
            'C':{
                'a_t':[0,0.2,0.4,0.6,0.8],
                'data':[[1.105 ,1.323 ,1.496 ,1.629 ,1.737],
                [1.000 ,1.153 ,1.271 ,1.369 ,1.462],
                [1.000 ,1.103 ,1.171 ,1.234 ,1.332],
                [1.000 ,1.063 ,1.096 ,1.149 ,1.247]]
            }
        }
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']

        target_point = np.array([[a / t]])
        # 配管継ぎ目付近にある亀裂
        table=ddf['A']
        X=table['a_t']
        data=table['data']
        F=[]
        for i in range(4):
            Y=data[i]
            krig = kr.Kriging()
            # np.arrayに変換
            xx = np.array(X, dtype=float).reshape(-1,1)
            yy = np.array(Y, dtype=float)
            krig.setData2(xx, yy)           # 入力と出力を標準化
            r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
            y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
            F.append(y_krig[0]) #予測値
        SA = F[0]*sigma0 + (2.0/np.pi)*F[1]*sigma1 + 0.5*F[2]*sigma2 + (4.0/(3.0*np.pi))*F[3]*sigma3
        KA = SA * np.sqrt(np.pi * a)
        # ノズル補強部にある亀裂
        table=ddf['B']
        X=table['a_t']
        data=table['data']
        F=[]
        for i in range(4):
            Y=data[i]
            krig = kr.Kriging()
            # np.arrayに変換
            xx = np.array(X, dtype=float).reshape(-1,1)
            yy = np.array(Y, dtype=float)
            krig.setData2(xx, yy)           # 入力と出力を標準化
            r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
            y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
            F.append(y_krig[0]) #予測値
        SB = F[0]*sigma0 + (2.0/np.pi)*F[1]*sigma1 + 0.5*F[2]*sigma2 + (4.0/(3.0*np.pi))*F[3]*sigma3
        KB = SB * np.sqrt(np.pi * a)
        # ノズルコーナー部にある亀裂
        table=ddf['C']
        X=table['a_t']
        data=table['data']
        F=[]
        for i in range(4):
            Y=data[i]
            krig = kr.Kriging()
            # np.arrayに変換
            xx = np.array(X, dtype=float).reshape(-1,1)
            yy = np.array(Y, dtype=float)
            krig.setData2(xx, yy)           # 入力と出力を標準化
            r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
            y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
            F.append(y_krig[0]) #予測値
        SC = F[0]*sigma0 + (2.0/np.pi)*F[1]*sigma1 + 0.5*F[2]*sigma2 + (4.0/(3.0*np.pi))*F[3]*sigma3
        KC = SC * np.sqrt(np.pi * a)

        res = {'KA': KA, 'KB': KB, 'KC': KC}
        super().SetRes(res)

class K_4_a_1(Base):
    def __init__(self):
        super().SetTitle('横腹の軸方向内表面半楕円表面き裂 Viswanatha らの解')

        super().SetRefer(
            "Viswanatha, N., Bhate, S. R., and Kushwaha, H. S.: Stress Intensity Factors for Elbows with Axial Surface Crack at Crown, " 
            "Transactions of the 14th International Conference on SMiRT, G06/5, p. 235, 1997"
        )

        # Applicable range: 0.2 ≤ a/t ≤ 0.8, 0.2 ≤ a/c ≤ 0.4, 0.75 ≤ R/Do ≤ 1.5, 9 ≤ Do/t ≤ 21

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        c = df['c']          # half surface crack length
        R = df['R']          # bend radius
        Do = df['Do']        # outer diameter
        p = df['p']          # internal pressure
        M = df['M']          # bending moment

        sigma_m = (Do / (2.0 * t)) * p
        sigma_bi = (4.0 / (np.pi * (Do ** 2) * t)) * M

        Q = 1.0 + 1.464 * (a / c) ** 1.65

        data = dm.Finput('K-4-a-1.csv')

        # 4D 変換用（ブロック順: (R/Do, Do/t) = (0.75,9),(0.75,21),(1.5,9),(1.5,21)）
        z1 = [0.75, 0.75, 1.5, 1.5]
        z2 = [9.0, 21.0, 9.0, 21.0]
        data_FmA=[]
        dd=[]
        for i in range(5):
            j=1+i*2
            data_FmA+=dm.extract_block(data,j)
        data_FbiA=[]
        dd=[]
        for i in range(5):
            j=2+i*2
            data_FbiA+=dm.extract_block(data,j)     




        # FmA（先頭4ブロック）
        X_m, W_m = dm.Fconv4D(data_FmA, z1, z2)
        r2_score = dm.KrigCalc(X_m, W_m)
        target_point = np.array([[a / t, a / c, R / Do, Do / t]])
        w_pred, _sigma = dm.Eval(target_point)
        FmA = w_pred

        # FbiA（次の4ブロック）
        X_bi, W_bi = dm.Fconv4D(data_FbiA, z1, z2)
        r2_score = dm.KrigCalc(X_bi, W_bi)
        w_pred, _sigma = dm.Eval(target_point)
        FbiA = w_pred

        # 最深点の応力拡大係数
        KA = (FmA * sigma_m + FbiA * sigma_bi) * np.sqrt(np.pi * a / Q)

        res = {'KA': KA}
        super().SetRes(res)

class K_4_a_2(Base):
    def __init__(self):
        super().SetTitle('横腹の軸方向内表面半楕円表面き裂 Mohan らの解')

        super().SetRefer(
            "Mohan, R., Krishna, A., Brust, F. W., Ghadiali, N., Kilinski, T., and Wilkowski, G. M.: Fracture Analysis of Cracked Elbows: "
            "Part I J-Estimation Schemes for Internal Circumferential and Axial Surface Cracks, ASME PVP, 323, p. 83, 1996 "
        )

        # Applicable range: 0.3 ≤ a/t ≤ 0.75, c/Dm ≈ 0.4, R/Dm ≈ 1.5, 10 ≤ Dm/t ≤ 40

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Dm = df['Dm']        # mean diameter
        p = df['p']          # internal pressure
        M = df['M']          # bending moment

        sigma_m = (Dm / (2.0 * t)) * p
        sigma_bi = 4.0 * M / (np.pi * (Dm ** 2) * t)

        data = dm.Finput('K-4-a-2.csv')
        target_point = np.array([[a / t, Dm / t]])

        X_1, W_1 = dm.CSV2XW(data, 1)
        r2_score = dm.KrigCalc(X_1, W_1)
        FmA, _sigma = dm.Eval(target_point)
        FmA = float(FmA)

        X_2, W_2 = dm.CSV2XW(data, 2)
        r2_score = dm.KrigCalc(X_2, W_2)
        FbiA, _sigma = dm.Eval(target_point)
        FbiA = float(FbiA)

        # 最深点の応力拡大係数
        KA = (FmA * sigma_m + FbiA * sigma_bi) * np.sqrt(np.pi * a)

        res = {'KA': KA}
        super().SetRes(res)

class K_4_b_1(Base):
    def __init__(self):
        super().SetTitle('横腹の軸方向貫通き裂 Kozluk らの解')

        super().SetRefer(
            "Kozluk, M. J., Manning, B. W., Misra, A. S., Lin, T. C., and Vijay, D. K.: "
            "Linear-Elastic Solutions for Long Radius Piping Elbows with Curvilinear Throughwall Cracks, ASME PVP, 143, p. 23, 1988"
        )

        # Applicable range: 0.1 ≤ c/Do ≤ 0.4, R/Do ≈ 1.5, 15 ≤ Do/t ≤ 100

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Do = df['Do']        # outside diameter
        R = df['R']          # bend radius
        p = df['p']          # internal pressure
        M = df['M']          # bending moment

        sigma_m = (Do / (2.0 * t)) * p
        sigma_bi = 4.0 * M / (np.pi * (Do ** 2) * t)

        data = dm.Finput('K-4-b-1.csv')
        target_point = np.array([[c / Do, Do / t]])

        # Wm
        X_1, W_1 = dm.CSV2XW(data, 1)
        r2_score = dm.KrigCalc(X_1, W_1)
        Wm, _sigma = dm.Eval(target_point)
        Wm = float(Wm)

        # Wbi
        X_2, W_2 = dm.CSV2XW(data, 2)
        r2_score = dm.KrigCalc(X_2, W_2)
        Wbi, _sigma = dm.Eval(target_point)
        Wbi = float(Wbi)

        Fm = (2.0 / np.sqrt(np.pi)) * (Do / t) ** 0.65 * (R / Do) ** (-0.65) * np.sqrt(Wm)
        Fbi = (np.sqrt(np.pi) / 4.0) * (Do / t) ** 0.65 * (R / Do) ** (-0.65) * np.sqrt(Wbi)

        K = (Fm * sigma_m + Fbi * sigma_bi) * np.sqrt(np.pi * c)

        res = {'K': K}
        super().SetRes(res)

class K_4_b_2(Base):
    def __init__(self):
        super().SetTitle('横腹の軸方向貫通き裂 Chattopadhyay らの解')

        super().SetRefer(
            "Chattopadhyay, J., Dutta, B. K., Kushwaha, H. S., Mahjan, S. C., and Kakodkar, A.: "
            "A Database to Evaluate Stress Intensity Factors of Elbows with Throughwall Flaws Under Combined Internal "
            "Pressure and Bending Moment, International Journal of Pressure Vessel and Piping, 60, p. 71, 1994"
        )

        # Applicable range: 0.11 ≤ c/Dm ≤ 0.4, 0.75 ≤ R/Dm ≤ 6.5, 10 ≤ Dm/t ≤ 40

    def Calc(self):
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # wall thickness
        Dm = df['Dm']        # mean diameter
        R = df['R']          # bend radius
        p = df['p']          # internal pressure

        sigma_m = (Dm / (2.0 * t)) * p

        h = 4.0 * R * t / (Dm ** 2)
        lambda_ = c / np.sqrt(Dm * t / 2.0)

        Fm = 0.5 * (0.5904 + 0.7452 * h ** 0.0974 + (-0.5249 + 0.5366 * h ** 0.027) * lambda_ ** 3.986
            + ((0.1675 + 0.1727 * h ** 0.0539) + (0.3639 + 0.6092 * h ** 0.0257) * lambda_ ** 0.9089)
            * (2.0 * t / Dm) ** (-0.2039))

        K = Fm * sigma_m * np.sqrt(np.pi * c)

        res = {'K': K}
        super().SetRes(res)

class K_4_c(Base):
    def __init__(self):
        super().SetTitle('背側の軸方向貫通き裂 Grebner–Hofler の解')
        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 3, EPRI NP-6301-D, 1991\n"
            "Grebner, H., and Hofler, A.: Analysis of a Pipe Elbow with Longitudinal Through-Crack, Nuclear Engineering and Design, 114, p. 147, 1989"
        )

        # Applicable range: 0.02 ≤ c/Do ≤ 0.6, R/Do ≈ 1.5, 15 ≤ Do/t ≤ 40

    def Calc(self):
        df = super().GetData()

        c  = df['c']          # half crack length
        t  = df['t']          # wall thickness
        Do = df['Do']         # outside diameter
        p  = df['p']          # internal pressure

        sigma_m = (Do/(2.0*t))*p
        Fm = 1.4029*np.sqrt(c/Do)*(Do/t)**0.36
        K  = Fm*sigma_m*np.sqrt(np.pi*c)

        res = {'K': K}
        super().SetRes(res)

class K_4_d(Base):
    def __init__(self):
        super().SetTitle('背側の周方向内表面半楕円表面き裂 Mohan らの解')

        super().SetRefer(
            "Mohan, R., Krishna, A., Brust, F. W., Ghadiali, N., Kilinski, T., and Wilkowski, G. M.: Fracture Analysis of Cracked Elbows: "
            "Part I J-Estimation Schemes for Internal Circumferential and Axial Surface Cracks, ASME PVP, 323, p. 83, 1996 "
        )

        # Applicable range: 0.3 ≤ a/t ≤ 0.75, c/Dm ≈ 0.8, R/Dm ≈ 1.5, 10 ≤ Dm/t ≤ 40

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # wall thickness
        Dm = df['Dm']        # mean diameter
        p = df['p']          # internal pressure
        M = df['M']          # bending moment

        sigma_m = (Dm / (2.0 * t)) * p
        sigma_bi = 4.0 * M / (np.pi * (Dm ** 2) * t)

        data = dm.Finput('K-4-d.csv')
        target_point = np.array([[a / t, Dm / t]])

        # FmA, FbiA
        for ith in range(1, 3):
            X_i, W_i = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_i, W_i)
            Fi, _sigma = dm.Eval(target_point)
            Fi = float(Fi)

            if ith == 1:
                FmA = Fi
            elif ith == 2:
                FbiA = Fi

        # 最深点の応力拡大係数
        KA = (FmA * sigma_m + FbiA * sigma_bi) * np.sqrt(np.pi * a)

        res = {'KA': KA}
        super().SetRes(res)

class K_4_e(Base):
    def __init__(self):
        super().SetTitle('背側の周方向貫通き裂 Chattopadhyay らの解')
        super().SetRefer('Chattopadhyay, J., Dutta, B. K., Kushwaha, H. S., Mahjan, S. C., and Kakodkar, A.: A Database to Evaluate Stress Intensity Factors of Elbows with Throughwall Flaws Under Combined Internal Pressure and Bending Moment, International Journal of Pressure Vessel and Piping, 60, p. 71, 1994')

        # Applicable range: 0.04 ≤ c/Dm ≤ 0.78, 0.19 ≤ R/Dm ≤ 6.5, 10 ≤ Dm/t ≤ 40

    def Calc(self):
        df = super().GetData()

        c = df['c']          # half surface crack length
        t = df['t']          # wall thickness
        Dm = df['Dm']        # mean diameter
        R = df['R']          # bend radius
        p = df['p']          # internal pressure
        M = df['M']          # bending moment

        sigma_m = (Dm/(2.0*t))*p
        sigma_bi = (4.0/(np.pi*Dm**2*t))*M

        h = (4.0*R*t)/(Dm**2)
        xi = (2.0/np.pi)*(c/Dm)
        tau = (2.0*t)/Dm

        Fm = 0.5 * (
            0.2510 + 0.2245*(h**-0.0405)
            + (-7.8911 + 5.2822*(h**0.1994))*(xi**1.3462)
            + ( (0.0773 + 0.0599*(h**0.0166)) + (0.5119 + 3.0222*(h**-0.3614))*(xi**1.2298) )*(tau**-0.3662)
        )

        Fbi = (
            -3.4628 + 4.446*(h**0.1366)
            + (-52.429 + 52.445*(h**-0.1848))*(xi**2.6137)
            + ( (-2.2524 + 1.1102*(h**0.1216)) + (0.8634 + 1.7283*(h**-0.3614))*(xi**0.4587) )*(tau**-0.5119)
        )

        K = (Fm*sigma_m + Fbi*sigma_bi)*np.sqrt(np.pi*c)

        res = {'K': K}
        super().SetRes(res)

class K_5_a(Base):
    def __init__(self):
        super().SetTitle('軸方向貫通き裂 Lin らの解')
        super().SetRefer(
            "Zahoor, A.: Ductile Fracture Handbook Volume 3, EPRI NP-6301-D, 1991\n"
            "Lin, T. C., Kozluk, M. J., Misra, A. S., and Gilbert, K. R.: Assessment of Throughwall Crack "
            "Tolerance of Darlington NGS 'A' Large Diameter Heat Transport Piping - Appendix C, Report No. 89511, "
            "Ontario Hydro, Tront, Canada, March, 1990"
        )
        # Applicable range: 0.05 ≤ c/rm ≤ 0.4, t/T ≈ 0.6, Rm/T ≈ 4.5, rm/T ≈ 4.5

    def Calc(self):
        df = super().GetData()

        c  = df['c']   # half surface crack length
        rm = df['rm']  # branch mean radius
        t  = df['t']   # branch wall thickness
        p  = df['p']   # internal pressure

        sigma_m = (rm / t) * p
        Fm = 2.3 + 1.25 * (c / rm)
        K = Fm * sigma_m * np.sqrt(np.pi * c)

        res = {'K': K}
        super().SetRes(res)

class K_5_b_1(Base):
    def __init__(self):
        super().SetTitle('周方向外表面半楕円表面き裂 Du-Hancock の解')
        super().SetRefer(
            'Du, Z.-Z., and Hancock, J. W.: Stress Intensity Factors of Semi-Elliptical Cracks '
            'in a Tubular Welded Joint Using Line Springs and 3D Finite Elements, '
            'Trans. ASME, J. of Pres. Ves. Technol., 111, p. 247, 1989'
        )

        # Applicable range: 0.2 ≤ a/T ≤ 0.9, c/T ≈ 0.2, t/T ≈ 0.8, Ro/T ≈ 14, ro/T ≈ 10, L/Ro ≈ 10

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']      # crack depth
        T = df['T']      # thickness (for a/T)
        t = df['t']      # thickness (for σm)
        ro = df['ro']    # radius ro
        P = df['P']      # load P

        sigma_m = P / (2.0 * np.pi * ro * t)

        data = dm.Finput('K-5-b-1.csv')

        X,Y=dm.extract_1D(data,1)#1ブロック目のデータを読む
        krig = kr.Kriging()
        # np.arrayに変換
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)

        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array([[a / T]], dtype=float))
        FmA=y_krig[0] #予測値


        # 最深点の応力拡大係数
        KA = FmA * sigma_m * np.sqrt(a)

        res = {'KA': KA}
        super().SetRes(res)

class K_5_b_2(Base):
    def __init__(self):
        super().SetTitle('周方向外表面半楕円表面き裂 Bowness-Lee の解')

        super().SetRefer(
            "Bowness, D., and Lee, M. M. K.: A Finite Element Study of Stress Fields and Stress Intensity Factors "
            "in Tublar Joints, Journal of Strain Analysis, 30, p. 135, 1995"
        )

        # Applicable range: 0.25 ≤ a/T ≤ 0.9, t/T ≈ 0.8, Ro/T ≈ 17, ro/T ≈ 8, L/Ro ≈ 20, H/Ro ≈ 6

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half crack length
        T = df['T']          # thickness (main pipe)
        P = df['P']          # load
        ro = df['ro']        # radius
        t = df['t']          # thickness

        sigma_m = P / (2.0 * np.pi * ro * t)
        Q = 1.0 + 1.464 * (a / c) ** 1.65

        data = dm.Finput('K-5-b-2.csv')
        target_point = np.array([[a / T]])

        X,Y=dm.extract_1D(data,1)#1ブロック目のデータを読む
        xq = 0.35 #この値に対する予測値を計算
        krig = kr.Kriging()
        # np.arrayに変換
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)

        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        FmA=y_krig[0] #予測値

        # 最深点の応力拡大係数
        KA = FmA * sigma_m * np.sqrt(np.pi * a / Q)

        res = {'KA': KA}
        super().SetRes(res)

class K_5_b_3(Base):
    def __init__(self):
        super().SetTitle('周方向外表面半楕円表面き裂 Olowokere-Nwosu の解')
        super().SetRefer(
            'Olowokere, D. O., and Nwosu, D. I.: Numerical Studies on Crack Growth in a Steel Tublar T-Joint, '
            'International Journal of Mechanical Science, 39, p. 859, 1997'
        )

        # Applicable range: 0.05 ≤ a/T ≤ 0.9, c/T ≈ 5, t/T ≈ 1, Ro/T ≈ 24, ro/T ≈ 12, L/Ro ≈ 3.5

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']        # crack depth
        T = df['T']        # thickness (used for a/T)
        t = df['t']        # thickness (used in stress definitions)
        ro = df['ro']      # radius ro
        P = df['P']        # axial force
        Mi = df['Mi']      # bending moment (inside)
        Mo = df['Mo']      # bending moment (outside)

        sigma_m = P / (2.0 * np.pi * ro * t)
        sigma_bi = Mi / (np.pi * (ro ** 2) * t)
        sigma_bo = Mo / (np.pi * (ro ** 2) * t)

        data = dm.Finput('K-5-b-3.csv')
        target_point = np.array([[a / T]])
        # FmA
        X,Y=dm.extract_1D(data,1)#1ブロック目のデータを読む
        krig = kr.Kriging()
        # np.arrayに変換
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)

        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        FmA=y_krig[0] #予測値
        # FboA
        X,Y=dm.extract_1D(data,2)#1ブロック目のデータを読む
        krig = kr.Kriging()
        # np.arrayに変換
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)

        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        FboA=y_krig[0] #予測値
        # FbiA
        X,Y=dm.extract_1D(data,3)#1ブロック目のデータを読む
        krig = kr.Kriging()
        # np.arrayに変換
        xx = np.array(X, dtype=float).reshape(-1,1)
        yy = np.array(Y, dtype=float)

        krig.setData2(xx, yy)           # 入力と出力を標準化
        r2 = krig.Fit(alpha=1e-6)     # 観測が滑らかなので小さめでOK
        y_krig, sigma_krig = krig.Predict2(np.array(target_point, dtype=float))
        FbiA=y_krig[0] #予測値

        # 最深点の応力拡大係数
        KA = (FmA * sigma_m + FbiA * sigma_bi + FboA * sigma_bo) * np.sqrt(np.pi * a)

        res = {'KA': KA}
        super().SetRes(res)

class K_6_a(Base):
    def __init__(self):
        super().SetTitle('内表面全周き裂 Fuhrey-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service,API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ Ri/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-6-a.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        # 応力拡大係数
        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)

class K_6_b(Base):
    def __init__(self):
        super().SetTitle('内表面全周き裂 Fuhrey-Osage の解')

        super().SetRefer(
            "American Petroleum Institute: Recommended Practice for Fitness-for-Service,API RP 579, 2000"
        )

        # Applicable range: 0 ≤ a/t ≤ 0.8, 2 ≤ Ri/t ≤ 1000

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        Ri = df['Ri']        # inner radius
        sigma0 = df['sigma0']
        sigma1 = df['sigma1']
        sigma2 = df['sigma2']
        sigma3 = df['sigma3']
        sigma4 = df['sigma4']

        data = dm.Finput('K-6-a.csv')
        target_point = np.array([[a / t, Ri / t]])

        F = np.zeros(5, dtype=float)            # F0..F4
        for ith in range(1, 6):                 # 1,2,3,4,5 (→ F0..F4)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        # 応力拡大係数
        S = F[0]*sigma0 + F[1]*sigma1*(a/t) + F[2]*sigma2*(a/t)**2 + F[3]*sigma3*(a/t)**3 + F[4]*sigma4*(a/t)**4
        K = S * np.sqrt(np.pi * a)

        res = {
            'K': K
        }
        super().SetRes(res)

class K_6_c(Base):
    def __init__(self):
        super().SetTitle('貫通き裂 Erdogan-Kibler の解')

        super().SetRefer(
            "Erdogan, F., and Kibler, J. J.: Cylindrical and Spherical Shells with Cracks, International Journal of Fracture Mechanics, 5, p. 229, 1969"
        )

        # Applicable range: 0 ≤ c/t ≤ 10, 10 ≤ Ri/t ≤ 20

    def Calc(self):
        dm = dmanage()
        df = super().GetData()

        c = df['c']          # half crack length
        t = df['t']          # thickness
        Ri = df['Ri']        # inner radius
        sigma_m = df['sigma_m']
        sigma_b = df['sigma_b']

        data = dm.Finput('K-6-c.csv')
        target_point = np.array([[c / t, Ri / t]])

        F = np.zeros(4, dtype=float)            # FmA, FbA, FmB, FbB
        for ith in range(1, 5):                 # 1,2,3,4 (→ FmA, FbA, FmB, FbB)
            X_ith, W_ith = dm.CSV2XW(data, ith)
            r2_score = dm.KrigCalc(X_ith, W_ith)
            Fi, _sigma = dm.Eval(target_point)
            F[ith - 1] = float(Fi)

        # 内表面における応力拡大係数
        KA = (F[0]*sigma_m + F[1]*sigma_b) * np.sqrt(np.pi * c)

        # 外表面における応力拡大係数
        KB = (F[2]*sigma_m + F[3]*sigma_b) * np.sqrt(np.pi * c)

        res = {
            'KA': KA,
            'KB': KB
        }
        super().SetRes(res)

class K_7_a(Base):
    def __init__(self):
        super().SetTitle('両側1/4楕円コーナーき裂 Raju-Newman の解')
        super().SetRefer(
            "Newman, J. C. Jr., and Raju, I. S.: Stress-Intensity Factor Equations for Cracks "
            "in Three-Dimensional Finite Bodies Subjected to Tension and Bending Loads, "
            "NASA Technical Memorandum 85793, NASA, 1984"
        )

        # Applicable range:
        # 0 < a/t < 1, 0.2 < a/c < 2, 0.5 < r/t < 2, 0 < (r + c)/b < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half crack length
        t = df['t']          # thickness
        b = df['b']          # half width
        r = df['r']          # corner radius
        P = df['P']          # axial force
        M = df['M']          # bending moment

        sigma_m = P / (2.0*b*t)
        sigma_b = 3.0*M / (b*t**2)

        at = a / t
        ac = a / c
        ca = c / a

        eps = 1.0e-12
        if abs(M) < eps:  # for tension
            mu = 0.85
        else:             # for bending
            mu = 0.85 - 0.25*at**0.25

        g1A = 1.0
        g1B = 1.1 + 0.35*at**2

        lambda_A = 1.0 / (1.0 + (c / r)*np.cos(mu*np.pi / 2.0))
        lambda_B = 1.0 / (1.0 + c / r)

        g2A = ( 1.0 + 0.358*lambda_A + 1.425*lambda_A**2 - 1.578*lambda_A**3 + 2.156*lambda_A**4) / (1.0 + 0.13*lambda_A**2)
        g2B = ( 1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.13*lambda_B**2)

        fw = np.sqrt(
            (1.0 / np.cos(np.pi*r / (2.0*b))) *
            (1.0 / np.cos((np.pi*(r + c) / (2.0*b))*np.sqrt(at)))
        )

        if ac <= 1.0:
            Q = 1.0 + 1.464*ac**1.65
            f_phi_A = 1.0
            f_phi_B = np.sqrt(ac)

            F0 = 1.13 - 0.09*ac + (-0.54 + 0.89 / (0.2 + ac))*at**2 + (0.5 - 1.0 / (0.65 + ac) + 14.0*(1.0 - ac)**24)*at**4

            g3A = 1.1*(1.0 + 0.04*ac)*(0.85 + 0.15*at**0.25)
            g3B = (1.0 + 0.04*ac)*(0.85 + 0.15*at**0.25)

            g4 = 1.0 - 0.7*(1.0 - at)*(ac - 0.2)*(1.0 - ac)

            HA = 1.0 + (-1.5 - 0.04*ac - 1.73*ac**2)*at 
            + (1.71 - 3.17*ac + 6.84*ac**2)*at**2 + (-1.28 + 2.71*ac - 5.22*ac**2)*at**3
            HB = 1.0 + (-0.43 - 0.74*ac - 0.84*ac**2)*at 
            + (1.25 - 1.19*ac + 4.39*ac**2)*at**2 + (-1.94 + 4.22*ac - 5.51*ac**2)*at**3

        else:
            Q = 1.0 + 1.464*ca**1.65
            f_phi_A = np.sqrt(ca)
            f_phi_B = 1.0

            F0 = ( np.sqrt(ca)*(1.0 + 0.04*ca) + 0.2*ca**4*at**2 - 0.11*ca**4*at**4)

            g3A = 1.1*(1.13 - 0.09*ca)*(0.85 + 0.15*at**0.25)
            g3B = (1.13 - 0.09*ca)*(0.85 + 0.15*at**0.25)

            g4 = 1.0

            HA = 1.0 + (-3.64 + 0.37*ca)*at 
            + (5.87 - 0.49*ca)*at**2 + (-4.32 + 0.53*ca)*at**3                      
            HB = 1.0 + (-2.07 + 0.06*ca)*at 
            + (4.35 + 0.16*ca)*at**2  + (-2.93 - 0.30*ca)*at**3

        FA = F0*g1A*g2A*g3A*g4*f_phi_A*fw
        FB = F0*g1B*g2B*g3B*g4*f_phi_B*fw

        #最深点の応力拡大係数
        KA = FA*(sigma_m + HA*sigma_b)*np.sqrt(np.pi*a / Q)
        #表面点の応力拡大係数
        KB = FB*(sigma_m + HB*sigma_b)*np.sqrt(np.pi*a / Q)

        res = {
            'KA': KA,
            'KB': KB
        }
        super().SetRes(res)

class K_7_b(Base):
    def __init__(self):
        super().SetTitle('片側1/4楕円コーナーき裂 Raju-Newman の解')
        super().SetRefer(
            "Newman, J. C. Jr., and Raju, I. S.: Stress-Intensity Factor Equations for Cracks in Three-Dimensional "
            "Finite Bodies Subjected to Tension and Bending Loads, NASA Technical Memorandum, 85793, NASA, 1984"
        )

        # Applicable range: 0 < a/t < 1, 0.2 < a/c < 2, 0.5 < r/t < 2, 0 < (r + c)/b < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        c = df['c']          # half crack length
        t = df['t']          # thickness
        b = df['b']          # half width
        r = df['r']          # corner radius
        P = df['P']          # axial force
        M = df['M']          # bending moment

        sigma_m = P / (2.0*b*t)
        sigma_b = 3.0*M / (b*t**2)

        at = a / t
        ac = a / c
        ca = c / a

        eps = 1.0e-12
        if abs(M) < eps:  # for tension
            mu = 0.85
        else:             # for bending
            mu = 0.85 - 0.25*at**0.25

        g1A = 1.0
        g1B = 1.1 + 0.35*at**2

        lambda_A = 1.0 / (1.0 + (c / r)*np.cos(mu*np.pi / 2.0))
        lambda_B = 1.0 / (1.0 + c / r)

        g2A = ( 1.0 + 0.358*lambda_A + 1.425*lambda_A**2 - 1.578*lambda_A**3 + 2.156*lambda_A**4) / (1.0 + 0.13*lambda_A**2)
        g2B = ( 1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.13*lambda_B**2)

        fw = np.sqrt(
            (1.0 / np.cos(np.pi*r / (2.0*b))) *
            (1.0 / np.cos((np.pi*(r + c) / (2.0*b))*np.sqrt(at)))
        )

        if ac <= 1.0:
            Q = 1.0 + 1.464*ac**1.65
            f_phi_A = 1.0
            f_phi_B = np.sqrt(ac)

            F0 = 1.13 - 0.09*ac + (-0.54 + 0.89 / (0.2 + ac))*at**2 + (0.5 - 1.0 / (0.65 + ac) + 14.0*(1.0 - ac)**24)*at**4

            g3A = 1.1*(1.0 + 0.04*ac)*(0.85 + 0.15*at**0.25)
            g3B = (1.0 + 0.04*ac)*(0.85 + 0.15*at**0.25)

            g4 = 1.0 - 0.7*(1.0 - at)*(ac - 0.2)*(1.0 - ac)

            HA = 1.0 + (-1.5 - 0.04*ac - 1.73*ac**2)*at 
            + (1.71 - 3.17*ac + 6.84*ac**2)*at**2 + (-1.28 + 2.71*ac - 5.22*ac**2)*at**3
            HB = 1.0 + (-0.43 - 0.74*ac - 0.84*ac**2)*at 
            + (1.25 - 1.19*ac + 4.39*ac**2)*at**2 + (-1.94 + 4.22*ac - 5.51*ac**2)*at**3

        else:
            Q = 1.0 + 1.464*ca**1.65
            f_phi_A = np.sqrt(ca)
            f_phi_B = 1.0

            F0 = ( np.sqrt(ca)*(1.0 + 0.04*ca) + 0.2*ca**4*at**2 - 0.11*ca**4*at**4)

            g3A = 1.1*(1.13 - 0.09*ca)*(0.85 + 0.15*at**0.25)
            g3B = (1.13 - 0.09*ca)*(0.85 + 0.15*at**0.25)

            g4 = 1.0

            HA = 1.0 + (-3.64 + 0.37*ca)*at 
            + (5.87 - 0.49*ca)*at**2 + (-4.32 + 0.53*ca)*at**3                      
            HB = 1.0 + (-2.07 + 0.06*ca)*at 
            + (4.35 + 0.16*ca)*at**2  + (-2.93 - 0.30*ca)*at**3

        FA = F0*g1A*g2A*g3A*g4*f_phi_A*fw
        FB = F0*g1B*g2B*g3B*g4*f_phi_B*fw

        factor = np.sqrt((4.0 / np.pi + a*c / (2.0*t*r)) / (4.0 / np.pi + a*c / (t*r)))

        #最深点の応力拡大係数
        KA_2cracks = FA*(sigma_m + HA*sigma_b)*np.sqrt(np.pi*a / Q)
        KA = factor*KA_2cracks

        #表面点の応力拡大係数
        KB_2cracks = FB*(sigma_m + HB*sigma_b)*np.sqrt(np.pi*a / Q)
        KB = factor*KB_2cracks

        res = {
            'KA': KA,
            'KB': KB,
        }
        super().SetRes(res)

class K_7_c(Base):
    def __init__(self):
        super().SetTitle('両側貫通き裂 Rooke–Cartwright の解')
        super().SetRefer("Rooke, D. P. and Cartwright, D. J.: Compendium of Stress Intensity Factors, Her Majesty's Stationary Office (HMSO), London, 1976")

        # Applicable range: 0 < c/r ≤ 1.0

    def Calc(self):
        df = super().GetData()

        c = df['c']          # half crack length along the hole edge
        r = df['r']          # hole radius
        b = df['b']          # half width
        t = df['t']          # plate thickness
        P = df['P']          # axial load
        M = df['M']          # bending moment

        sigma_m = P / (2.0 * b * t)
        sigma_b = 3.0 * M / (b * t**2)

        Zeta = c / r

        Fm = (0.19806 + 18.886*Zeta + 18.713*Zeta**2 + 26.651*Zeta**3) / (1.0 + 15.144*Zeta + 19.136*Zeta**2 + 26.629*Zeta**3)
        Fb = 0.4 * (-0.007089 - 1.2934*Zeta + 0.2442*Zeta**2 - 0.058739*Zeta**2.5 + 2.0789*Zeta**0.5)

        # 応力拡大係数
        K = (Fm * sigma_m + Fb * sigma_b) * np.sqrt(np.pi * c)

        res = {'K': K}
        super().SetRes(res)

class K_7_d(Base):
    def __init__(self):
        super().SetTitle('片側貫通き裂 Rooke–Cartwright の解')
        super().SetRefer("Rooke, D. P. and Cartwright, D. J.: Compendium of Stress Intensity Factors, Her Majesty’s Stationary Office (HMSO), London, 1976")

        # Applicable range: 0 < c/r ≤ 1.0

    def Calc(self):
        df = super().GetData()

        c = df['c']          # crack length
        r = df['r']          # hole radius
        t = df['t']          # plate thickness
        b = df['b']          # half width
        P = df['P']          # axial load
        M = df['M']          # bending moment

        sigma_m = P/(2.0*b*t)
        sigma_b = 3.0*M/(b*t**2)

        zeta = c/r
        Fm = (3.3539 + 7.7313*zeta + 4.9282*zeta**2) / (1.0 + 4.3586*zeta + 6.9091*zeta**2)
        Fb = 0.4*(-0.006327 - 1.2904*zeta + 0.16219*zeta**2 - 0.011274*zeta**3 + 2.07*zeta**0.5)

        K = (Fm*sigma_m + Fb*sigma_b)*np.sqrt(np.pi*c)

        res = {'K': K}
        super().SetRes(res)

class K_7_e(Base):
    def __init__(self):
        super().SetTitle('両側内部半楕円き裂 Raju-Newman の解')

        super().SetRefer(
            "Newman, J. C. Jr., and Raju, I. S.: Stress-Intensity Factor Equations for Cracks in Three-Dimensional Finite Bodies Subjected to Tension and Bending Loads, NASA Technical Memorandum, 85793, NASA, 1984"
        )

        # Applicable range: 0 < a/t < 1, 0.2 < a/c < 2, 0.5 < r/t <= 2, 0 < (r+c)/b < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']  # crack depth
        c = df['c']  # half crack length
        t = df['t']  # thickness
        b = df['b']  # half width
        r = df['r']  # notch radius
        P = df['P']  # tensile load

        sigma_m = P / (2.0 * b * t)

        at = a / t
        ac = a / c
        ca = c / a

        g1A = 1.0
        g1B = 1.0 - (at**4) * np.sqrt(2.6 - 2.0 * at) / (1.0 + 4.0 * ac)

        lambda_A = 1.0 / (1.0 + (c / r) * np.cos(0.45 * np.pi))
        lambda_B = 1.0 / (1.0 + c / r)
        
        g2A = (1.0 + 0.358*lambda_A + 1.425*lambda_A**2 - 1.578*lambda_A**3 + 2.156*lambda_A**4) / (1.0 + 0.08*lambda_A**2)
        g3A = 1.0 + 0.1 * at**10
        g3B = 1.0

        fw = np.sqrt((1.0 / np.cos(np.pi * r / (2.0 * b))) * (1.0 / np.cos((np.pi * (r + c) / (2.0 * b)) * np.sqrt(a / t))))

        if ac <= 1.0:
            Q = 1.0 + 1.464 * ac**1.65
            f_phi_A = 1.0
            f_phi_B = np.sqrt(ac)
            F0 = 1.0 + (0.05 / (0.11 + ac**1.5)) * at**2 + (0.29 / (0.23 + ac**1.5)) * at**4
            g2B = (1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.08*lambda_B**2)

        else:
            Q = 1.0 + 1.464 * ca**1.65
            f_phi_A = np.sqrt(ca)
            f_phi_B = 1.0
            F0 = np.sqrt(ca) + (0.05 / (0.11 + ac**1.5)) * at**2 + (0.29 / (0.23 + ac**1.5)) * at**4           
            g2B = (1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.13*lambda_B**2)

        FmA = F0 * g1A * g2A * g3A * f_phi_A * fw
        FmB = F0 * g1B * g2B * g3B * f_phi_B * fw

        #最深点の応力拡大係数
        K_A = FmA * sigma_m * np.sqrt(np.pi * a / Q)
        #表面点の応力拡大係数
        K_B = FmB * sigma_m * np.sqrt(np.pi * a / Q)

        res = {
            'K_A': K_A,
            'K_B': K_B
        }
        super().SetRes(res)

class K_7_f(Base):
    def __init__(self):
        super().SetTitle('片側内部半楕円き裂 Raju-Newman の解')

        super().SetRefer(
            "Newman, J. C. Jr., and Raju, I. S.: Stress-Intensity Factor Equations for Cracks in Three-Dimensional Finite Bodies Subjected to Tension and Bending Loads, NASA Technical Memorandum, 85793, NASA, 1984"
        )

        # Applicable range: 0 < a/t < 1, 0.2 < a/c < 2, 0.5 < r/t <= 2, 0 < (r+c)/b < 0.5

    def Calc(self):
        df = super().GetData()

        a = df['a']  # crack depth
        c = df['c']  # half crack length
        t = df['t']  # thickness
        b = df['b']  # half width
        r = df['r']  # notch radius
        P = df['P']  # tensile load

        sigma_m = P / (2.0 * b * t)

        at = a / t
        ac = a / c
        ca = c / a

        g1A = 1.0
        g1B = 1.0 - (at**4) * np.sqrt(2.6 - 2.0 * at) / (1.0 + 4.0 * ac)

        lambda_A = 1.0 / (1.0 + (c / r) * np.cos(0.45 * np.pi))
        lambda_B = 1.0 / (1.0 + c / r)
        
        g2A = (1.0 + 0.358*lambda_A + 1.425*lambda_A**2 - 1.578*lambda_A**3 + 2.156*lambda_A**4) / (1.0 + 0.08*lambda_A**2)
        g3A = 1.0 + 0.1 * at**10
        g3B = 1.0

        fw = np.sqrt((1.0 / np.cos(np.pi * r / (2.0 * b))) * (1.0 / np.cos((np.pi * (r + c) / (2.0 * b)) * np.sqrt(a / t))))

        if ac <= 1.0:
            Q = 1.0 + 1.464 * ac**1.65
            f_phi_A = 1.0
            f_phi_B = np.sqrt(ac)
            F0 = 1.0 + (0.05 / (0.11 + ac**1.5)) * at**2 + (0.29 / (0.23 + ac**1.5)) * at**4
            g2B = (1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.08*lambda_B**2)

        else:
            Q = 1.0 + 1.464 * ca**1.65
            f_phi_A = np.sqrt(ca)
            f_phi_B = 1.0
            F0 = np.sqrt(ca) + (0.05 / (0.11 + ac**1.5)) * at**2 + (0.29 / (0.23 + ac**1.5)) * at**4           
            g2B = (1.0 + 0.358*lambda_B + 1.425*lambda_B**2 - 1.578*lambda_B**3 + 2.156*lambda_B**4) / (1.0 + 0.13*lambda_B**2)

        FmA = F0 * g1A * g2A * g3A * f_phi_A * fw
        FmB = F0 * g1B * g2B * g3B * f_phi_B * fw

        factor = np.sqrt(((4.0 / np.pi) + (a * c) / (2.0 * t * r)) / ((4.0 / np.pi) + (a * c) / (t * r)))

        #最深点の応力拡大係数
        KA_2cracks = FmA * sigma_m * np.sqrt(np.pi * a / Q)
        KA = factor * KA_2cracks

        #表面点の応力拡大係数
        KB_2cracks = FmB * sigma_m * np.sqrt(np.pi * a / Q)
        KB = factor * KB_2cracks

        res = {
            'KA': KA,
            'KB': KB
        }
        super().SetRes(res)

class K_8_a(Base):
    def __init__(self):
        super().SetTitle('丸棒の周方向全周表面き裂 Tada らの解')
        super().SetRefer('Tada, H., Paris, P. C., and Irwin, G. R.: The Stress Analysis of Cracks Handbook -Second Edition,Paris Production Inc.,St. Louis,Missouri,1985')

        # Applicable range: 0 ≤ a/Ro < 1

    def Calc(self):
        df = super().GetData()

        Ro = df['Ro']        # bar radius
        a  = df['a']         # crack depth
        P  = df['P']         # axial load
        M  = df['M']         # bending moment

        zeta = 1.0 - a/Ro

        Fm = 0.5 * np.sqrt(zeta) * (
            1.0 + 0.5*zeta + 0.375*zeta**2 - 0.363*zeta**3 + 0.731*zeta**4
        )
        Fb = 0.375 * np.sqrt(zeta) * (
            1.0 + 0.5*zeta + 0.375*zeta**2 + 0.313*zeta**3 + 0.273*zeta**4 + 0.537*zeta**5
        )

        sigma_m = P/(np.pi*Ro**2)
        sigma_b = 4.0*M/(np.pi*Ro**3)

        K = (Fm*sigma_m + Fb*sigma_b) * np.sqrt(np.pi*a)

        res = {'K': K}
        super().SetRes(res)

class K_8_b(Base):
    def __init__(self):
        super().SetTitle('丸棒の周方向直線前縁表面き裂  Sih の解')
        super().SetRefer('Sih, G. C.: Handbook of Stress Intensity Factors, Institute of Fracture and Solid Mechanics, Lehigh University, Bethlehem, Pa.')

        # Applicable range: 0.125 ≤ a/Ro ≤ 1.25

    def Calc(self):
        df = super().GetData()

        a  = df['a']   # crack depth
        Ro = df['Ro']  # bar radius
        P  = df['P']   # axial load
        M  = df['M']   # bending moment

        sigma_m = P/(np.pi*Ro**2)
        sigma_b = 4.0*M/(np.pi*Ro**3)

        zeta = a/(2.0*Ro)

        Fm = 0.926 - 1.771*zeta + 26.421*zeta**2 - 78.481*zeta**3 + 87.911*zeta**4
        Fb = 1.040 - 3.640*zeta + 16.860*zeta**2 - 32.590*zeta**3 + 28.410*zeta**4

        K = (Fm*sigma_m + Fb*sigma_b)*np.sqrt(np.pi*a)

        res = {'K': K}
        super().SetRes(res)

class K_8_c(Base):
    def __init__(self):
        super().SetTitle('丸棒の周方向半円表面き裂 API の解')
        super().SetRefer('American Petroleum Institute: Recommended Practice for Fitness-for-Service, API RP 579, 2000')

        # Applicable range: 0 < a/Ro ≤ 1.2

    def Calc(self):
        df = super().GetData()

        a  = df['a']   # crack depth
        Ro = df['Ro']  # bar radius
        P  = df['P']   # axial load
        M  = df['M']   # bending moment

        sigma_m = P/(np.pi*Ro**2)
        sigma_b = 4.0*M/(np.pi*Ro**3)

        zeta = a/(2.0*Ro)
        psi  = np.pi*a/(4.0*Ro)

        g = (1.84/np.pi) * (np.tan(psi)/psi)**0.5 / np.cos(psi)

        Fm = g*(0.752 + 2.02*zeta + 0.37*(1.0 - np.sin(psi))**3)
        Fb = g*(0.953 + 0.199*(1.0 - np.sin(psi))**4)

        K = (Fm*sigma_m + Fb*sigma_b)*np.sqrt(np.pi*a)

        res = {'K': K}
        super().SetRes(res)

class K_8_d(Base):
    def __init__(self):
        super().SetTitle('ボルトの周方向直線前縁表面き裂 James-Mills の解')
        super().SetRefer('James, L. A. and Mills, W. J.: Review and Synthesis of Stress Intensity Factor Solutions Applicable to Cracks in Bolts, Engineering Fracture Mechanics, 30, 5, p. 641, 1988')

        # Applicable range: 0.008 ≤ a/Rth ≤ 1

    def Calc(self):
        df = super().GetData()

        a   = df['a']        # crack depth
        Rth = df['Rth']      # screw groove radius (effective radius)
        P   = df['P']        # axial load
        M   = df['M']        # bending moment

        sigma_m = P/(np.pi*Rth**2)
        sigma_b = 4.0*M/(np.pi*Rth**3)

        zeta = a/(2.0*Rth)

        Fm = 2.043*np.exp(-31.332*zeta) + 0.6507 + 0.5367*zeta + 3.0469*zeta**2 - 19.504*zeta**3 + 45.647*zeta**4
        Fb = 0.6301 + 0.03488*zeta - 3.3365*zeta**2 + 13.406*zeta**3 - 6.0021*zeta**4

        K = (Fm*sigma_m + Fb*sigma_b)*np.sqrt(np.pi*a)

        res = {'K': K}
        super().SetRes(res)


class L_1_a(Base):
    def __init__(self):
        super().SetInputItems(['a','b','t','P','M','c','Sy'])
        super().SetTitle('平板の亀裂，半楕円表面亀裂')
        super().SetRefer('Dillstrom,P.andSattari-Far,I.:Limit Load Solutions for Surface Cracks in Plates and Cylinders, RSE R & D Report,No.2002/01,Det Norske Veritas AB 2002')
    def Calc(self):
        df=super().GetData()
        w=df['b']
        a=df['a']
        t=df['t']
        P=df['P']
        M=df['M']
        l=df['c']*2
        Sy=df['Sy']
        Sm=P/(2*w*t)
        Sb=3*M/(w*t*t)
        z=a*l/(t*(l+2*t))
        Lr=((1-z)**1.58*Sb/3+np.sqrt((1-z)**3.16*Sb*Sb/9+(1-z)**3.14*Sm*Sm))/((1-z)**2*Sy)
        res={'Lr':Lr}
        super().SetRes(res)
class L_1_b(Base):
    def __init__(self):
        super().SetTitle('長い表面き裂（片側）')
        super().SetRefer('Willoughby, A. A. and Davey, T. G.: ASTM STP 1020, ASTM, Philadelphia, pp.390-409, 1989')

        # Applicable range: a/t <= 0.8 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        w = df['w']          # half width
        P = df['P']          # axial load
        M = df['M']          # bending moment
        Sy = df['Sy']        # yield stress

        sigma_m = P / (2.0 * w * t)
        sigma_b = 3.0 * M / (w * t**2)
        zeta = a / t

        Lr = (zeta * sigma_m + sigma_b / 3.0 + np.sqrt((zeta * sigma_m + sigma_b / 3.0)**2 + (1.0 - zeta)**2 * sigma_m**2)) / ((1.0 - zeta)**2 * Sy)

        res = {'Lr': Lr}
        super().SetRes(res)
class L_1_c(Base):
    def __init__(self):
        super().SetTitle('長い表面き裂（両側）')
        super().SetRefer('Miller, A. G.: Review of Limit Loads of Structures Containing Defects, Int. J. Pres. Ves. and Piping, 32 p.197, 1988')

        # 寸法および負荷レベルに応じたき裂面の接触状態を考慮して使い分ける

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        w = df['w']          # half width
        P = df['P']          # axial load
        M = df['M']          # bending moment
        Sy = df['Sy']        # yield stress

        # 片側のき裂面が完全に接触する場合(criterion>0)
        b1 = t - a
        M1 = M + P * a / 2.0

        Lr1 = (2.0 * M1 + np.sqrt(4.0 * M1**2 + (P**2) * (b1**2))) / (Sy * b1**2)

        criterion = b1 - 2.0 * a - P / (Lr1 * Sy)
        x = 2 * b1 - 2 * a - P/(Lr1 * Sy)

        if criterion <= 0.0:  # 片側のき裂面が部分的に接触する場合
            Mp = M1 - P * (b1 - x) / 2.0
            Lr = (2.0 * Mp + np.sqrt(4.0 * Mp**2 + (P**2) * (x**2))) / (Sy * x**2)
        else:
            Lr = Lr1

        res = {'Lr': Lr}
        super().SetRes(res)        
class L_1_d(Base):
    def __init__(self):
        super().SetTitle('貫通き裂')
        super().SetRefer('Milne, I., et al.: CEGB Rep., R/H/R6-Rev.3, p.A2.6, 1986')

    def Calc(self):
        df = super().GetData()

        w = df['w']          # half width
        l = df['l']          # crack length
        e = df['e']          # eccentricity
        P = df['P']          # axial load per thickness
        M = df['M']          # bending moment per thickness
        Sy = df['Sy']        # yield stress

        A1 = (4.0 * w**2 - l**2) / 4.0 - l * e
        A2 = (4.0 * w**2 - l**2) / 4.0 + l * e

        Lr1 = (np.abs(M + l * P / 2.0) + np.sqrt((M + l * P / 2.0)**2 + P**2 * A1)) / (2.0 * Sy * A1)
        Lr2 = (np.abs(M - l * P / 2.0) + np.sqrt((M - l * P / 2.0)**2 + P**2 * A2)) / (2.0 * Sy * A2)

        criterion1 = M / (2.0 * w * P) + l * e / (2.0 * w * (2.0 * w - l ))
        criterion2 = M / (2.0 * w * P) + (4.0 * w**2 - l**2 - 4.0 * e**2) / (16.0 * e * w)
 
        if (criterion1 >= 0.0 and criterion2 >= 0.0) or (criterion1 <= 0.0 and criterion2 <= 0.0):
            Lr = Lr1
        else:
            Lr = Lr2

        res = {'Lr': Lr}
        super().SetRes(res)        
class L_1_e(Base):
    def __init__(self):
        super().SetTitle('楕円内部き裂')
        super().SetRefer('Willoughby, A. A. and Davey, T. G.: ASTM STP 1020, ASTM, Philadelphia, pp.390-409, 1989')

        # Applicable range: 2a/t <= 0.8, c/t >= 0 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        w = df['w']          # half width
        l = df['l']          # crack length parameter
        e = df['e']          # eccentricity
        P = df['P']          # axial load
        M = df['M']          # bending moment
        Sy = df['Sy']        # yield stress

        sigma_m = P / (2.0 * w * t)
        sigma_b = 3.0 * M / (w * t**2)

        zeta = 2.0 * a * l / (t * (l + 2.0 * t))
        gamma = 0.5 - a / t - e / t

        # 局部崩壊
        Lr = (zeta * sigma_m + sigma_b / 3.0 + np.sqrt((zeta * sigma_m + sigma_b / 3.0)**2 + (((1.0 - zeta)**2 + 4.0 * zeta * gamma) * sigma_m**2))) / (((1.0 - zeta)**2 + 4.0 * zeta * gamma) * Sy)

        res = {'Lr': Lr}
        super().SetRes(res)
class L_2_a(Base):
    def __init__(self):
        super().SetTitle('軸方向内表面半楕円表面き裂')
        super().SetRefer('内圧p：Chell, G. G.: TPRD/L/MT0237/M84, ADISC, CEGB, 1984' \
        '膜応力σm： Dillström, P. and Sattari-Far, I.: Limit Load Solutions for Surface Cracks in Plates and Cylinders, RSE R&D Report, No.2002/01, Det Norske Veritas AB, 2002')

        # Applicable range: 内圧p：記述はないが経験式のため制限はあると考えられる　膜応力σm：a/t <= 0.8 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        l = df['l']          # crack length parameter
        Ri = df['Ri']        # inner radius
        p = df['p']          # internal pressure
        Sy = df['Sy']        # yield stress

        Rm = Ri + t / 2.0
        eta = 1.0 - a / t
        p0 = Sy * (t / Rm)

        m = (1.0 + 1.61 * (1.0 - eta) * l**2 / (4.0 * t * Rm))**0.5
        pc1 = p0 * (eta / (1.0 - (1.0 - eta) / m))

        mp = (1.0 + 1.61 * l**2 / (4.0 * t * Rm))**0.5
        pc2 = p0 * (eta + (1.0 - eta) / mp)

        Lr_p1 = p / pc1 #内圧・局部崩壊
        Lr_p2 = p / pc2 #内圧・全体崩壊

        zeta = 2.0 * a * l / (t * (l + 2.0 * t))
        sigma_m = p *Rm / t
        Lr_sm = (1.0 / np.sqrt((1.0 - zeta**3.11)**1.9)) * (sigma_m / Sy) #膜応力・局部崩壊

        res = {'Lr_p1': Lr_p1,'Lr_p2': Lr_p2,'Lr_sm': Lr_sm }
        super().SetRes(res)
        
class L_2_b(Base):
    def __init__(self):
        super().SetInputItems(['a','t','Ri','p','Sy'])
        super().SetTitle('軸方向内表面長い表面亀裂')
        super().SetRefer('Kumar V.,German M.D. and Shih C.F.:EPRI NP-1931,Electric Power Research Institute, Palo Alto,CA,July 1981')
    def Calc(self):
        df=super().GetData()
        a=df['a']
        t=df['t']
        Sy=df['Sy']
        Ri=df['Ri'] 
        p=df['p']
        z=a/t
        p0=(2/np.sqrt(3))*Sy*(t/Ri)
        pc=p0*((1-z)/(1+z/(Ri/t)))
        Lr=p/pc
        res={'Lr':Lr,
             'pc':pc}
        super().SetRes(res)
class L_2_c(Base):
    def __init__(self):
        super().SetTitle('軸方向外表面半楕円表面き裂')
        super().SetRefer('Dillström, P. and Sattari-Far, I.: Limit Load Solutions for Surface Cracks in Plates and Cylinders, RSE R&D Report, No.2002/01, Det Norske Veritas AB, 2002')

        # Applicable range: a/t <= 0.8 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        l = df['l']          # crack length parameter
        sigma_m = df['sigma_m']  # membrane stress
        Sy = df['Sy']        # yield stress
    
        zeta = a * l / (t * (l + 2.0 * t))

        Lr = (1.0 / np.sqrt((1.0 - zeta**3.11)**1.9)) * (sigma_m / Sy)

        res = {'Lr': Lr}
        super().SetRes(res)
class L_2_d(Base):
    def __init__(self):
        super().SetTitle('軸方向外表面長い表面き裂')
        super().SetRefer('Willoughby, A. A. and Davey, T. G.: ASTM STP 1020, ASTM, Philadelphia, pp.390-409, 1989')

        # Applicable range: a/t <= 0.8 

    def Calc(self):
        df = super().GetData()

        a = df['a']          # crack depth
        t = df['t']          # thickness
        sigma_m = df['sigma_m']  # membrane stress
        sigma_b = df['sigma_b']  # bending stress
        sigma_y = df['Sy']  # yield stress

        zeta = a / t

        Lr = (zeta * sigma_m + sigma_b / 3.0 + np.sqrt((zeta * sigma_m + sigma_b / 3.0)**2 + (1.0 - zeta)**2 * sigma_m**2)) / ((1.0 - zeta)**2 * sigma_y)

        res = {'Lr': Lr}
        super().SetRes(res)
class L_2_e(Base):
    def __init__(self):
        super().SetTitle('軸方向貫通き裂')
        super().SetRefer('内圧：Zahoor A.: Ductile Fracture Handbook, Vol.2, Novetech Corporation and Electric Power Research Institute, 1989' \
        '膜応力： Kiefner, J. F., et al.: ASTM STP 536, ASTM, Philadelphia, Pa., pp.461-481, 1973')

        # Applicable range:内圧： 0 <= lambda <= 5, 膜応力：き裂長さに比較して円筒が十分長く端部効果を無視できること 

    def Calc(self):
        df = super().GetData()

        t = df['t']          # thickness
        Ri = df['Ri']        # inner radius
        l = df['l']          # crack length
        p = df['p']          # internal pressure
        sigma_m = df['sigma_m']  # membrane stress
        Sy = df['Sy']  # yield stress

        Rm = Ri + t / 2.0

        # 内圧
        lambda_p = l / (2.0 * np.sqrt(Rm * t))
        m = (1.0 + 1.2987 * lambda_p**2 - 0.026905 * lambda_p**4 + 5.3549e-4 * lambda_p**6)**0.5
        pc = Sy * (t / Rm) / m
        Lr_p = p / pc

        # 膜応力
        lambda_sm = l / (2.0 * np.sqrt(Ri * t))
        Lr_sm = (sigma_m / Sy) * np.sqrt(1.0 + 1.05 * lambda_sm**2)

        res = {'Lr_p': Lr_p, 'Lr_sm': Lr_sm}
        super().SetRes(res)
class L_2_k(Base):
    def __init__(self):
        super().SetTitle('周方向貫通き裂')
        super().SetRefer(
            '・軸力P\n'
            'Zahoor A. and Norris D. M.: ASME J. PVT, Vol.106, pp.399-404, 1984\n'
            'Zahoor A.: Final Report on EPRI Project, T118-9-1, December 1982\n'
            '・曲げモーメントM\n'
            'Kanninen M. F., et al.: EPRI NP-2347, Vols. 1 and 2, EPRI, Palo Alto, CA, April 1982\n'
            '・軸力Pと曲げモーメントM\n'
            'Kanninen M. F., et al.: EPRI NP-2347, Vols. 1 and 2, EPRI, Palo Alto, CA, April 1982\n'
            'Kanninen M. F. et al.: Nuclear Engineering and Design, Vol.48, pp.117-134, 1978\n'
            '・膜応力σmと管曲げ応力σbg\n'
            'Kanninen M. F., et al.: EPRI NP-192, EPRI, Palo Alto, CA, 1976'
        )

        # [適用範囲]
        # ・軸力P
        #   薄肉配管であること。
        # ・曲げモーメントM
        #   薄肉および厚肉の配管に適用できる。
        # ・軸力Pと曲げモーメントM
        #   薄肉および厚肉の配管に適用できるが，軸力Pは下式を満たすこと。
        #   P/(2πRmtσY) ≦ 0.25
        # ・膜応力σmと管曲げ応力σbg
        #   円筒は薄肉で，膜応力成分が曲げ応力成分に比較して十分小さいこと。

    def Calc(self):
        df = super().GetData()

        l  = df['l']          # crack length (l = 2 Rm θ)
        t  = df['t']          # thickness
        Ri = df['Ri']         # inner radius
        P  = df.get('P', 0.0) # axial force
        M  = df.get('M', 0.0) # bending moment
        sigma_m  = df.get('sigma_m', 0.0)   # membrane stress
        sigma_bg = df.get('sigma_bg', 0.0)  # pipe bending stress
        Sy = df['Sy']         # yield stress

        Ro = Ri + t
        Rm = Ri + t / 2.0
        zeta = t / Ro

        # 軸力 P
        theta_P = (l / 2.0) / Ri
        alpha_P = np.arccos(np.clip(0.5 * np.sin(theta_P), -1.0, 1.0))
        P0 = (2.0 - zeta) * np.pi * Ro * t * Sy
        Pc = P0 * (2.0 * alpha_P - theta_P) / np.pi

        Lr_P = P / Pc

        # 曲げモーメント M
        theta_M = (l / 2.0) / Rm

        if (Rm / t) < 10.0:
            alpha_M = 0.5 * theta_M * (1.0 - zeta) * (1.0 + 0.5 * zeta / (1.0 - zeta)) / (1.0 - 0.5 * zeta)
            Mc_M = 4.0 * Sy * (Ro ** 2) * t * (1.0 - zeta + zeta ** 2 / 3.0) * (np.cos(alpha_M) - 0.5 * np.sin(theta_M))
        else:
            Mc_M = 4.0 * Sy * (Rm ** 2) * t * (np.cos(theta_M / 2.0) - 0.5 * np.sin(theta_M))

        Lr_M = M / Mc_M

        # 軸力 P と 曲げモーメント M
        if (Rm / t) < 10.0:
            alpha_PM = 0.5 * theta_M * (1.0 - zeta) * (1.0 + 0.5 * zeta / (1.0 - zeta)) / (1.0 - 0.5 * zeta) + P / (4.0 * Sy * Ro * t * (1.0 - zeta))
            Mc_PM = 4.0 * Sy * (Ro ** 2) * t * (1.0 - zeta + zeta ** 2 / 3.0) * (np.cos(alpha_PM) - 0.5 * np.sin(theta_M))
        else:
            alpha_PM = theta_M / 2.0 + P / (4.0 * Sy * Rm * t)
            Mc_PM = 4.0 * Sy * (Rm ** 2) * t * (np.cos(alpha_PM) - 0.5 * np.sin(theta_M))

        Lr_PM = M / Mc_PM

        # 膜応力 σm と 管曲げ応力 σbg
        theta_s = l / (2.0 * Ri)
        term_P = (sigma_m / Sy) * (np.pi / (np.pi - theta_s - 2.0 * np.arcsin(np.clip(0.5 * np.sin(theta_s), -1.0, 1.0))))
        term_M = (sigma_bg / Sy) * (np.pi * (1.0 - (t / Ri) / ((1.0 + t / Ri) * (2.0 + t / Ri))) / (4.0 * np.sin(np.pi / 2.0 - l / (4.0 * Ri)) - 0.5 * np.sin(theta_s))) 

        Lr_sm_bg = term_P + term_M

        res = {
            'Lr_P': Lr_P,
            'Lr_M': Lr_M,
            'Lr_PM': Lr_PM,
            'Lr_sm_bg': Lr_sm_bg
        }
        super().SetRes(res)
class L_3_b(Base):
    def __init__(self):
        super().SetTitle('軸方向内表面1/4円コーナ表面き裂')
        super().SetRefer(
            'Lind, N. C.: ASME Paper 67-WA/PVP-7, ASME, New York, pp.951-958, 1967\n'
            'Rodabaugh, E. C., et al.: TID-24342, USAEC, March, 1966-December, 1967'
        )

        # 適用範囲 : a/√(4As/π) ≦ 0.8

    def Calc(self):
        df = super().GetData()

        a   = df['a']           # crack size (1/4 circle radius)
        Ris = df['Ris']         # inside radius (nozzle pipe)
        Rim = df['Rim']         # inside radius (main pipe)
        tn  = df['tn']          # nozzle thickness
        tm  = df['tm']          # shell thickness (main)
        p   = df['p']           # internal pressure
        Sy  = df['Sy']          # yield stress

        ls = 0.5 * np.sqrt(Ris * tn)

        # 球形圧力容器
        lm_sph = np.minimum(0.5 * np.sqrt(Rim * tm), (tm + tn))
        As_sph = lm_sph * tm + ls * tn
        Ap_sph = (Rim + tm + ls) * (Ris + lm_sph) - ls * (lm_sph - tn)

        Lr_sph = (p / Sy) * (Ap_sph / (As_sph - (np.pi * a**2 / 4.0)))

        # 円筒型圧力容器  
        lm_cyl = np.maximum(0.5 * np.sqrt(Rim * tm), 2.0 * (tm + tn) / 3.0)
        As_cyl = lm_cyl * tm + ls * tn
        Ap_cyl = (Rim + tm + ls) * (Ris + lm_cyl) - ls * (lm_cyl - tn)

        Lr_cyl = (p / Sy) * (Ap_cyl / (As_cyl - (np.pi * a**2 / 4.0)))

        res = {'Lr_sph': Lr_sph, 'Lr_cyl': Lr_cyl}
        super().SetRes(res)
class L_6_c(Base):
    def __init__(self):
        super().SetTitle('貫通き裂')
        super().SetRefer('Burdekin, F. M. and Taylor, T. E.: J. Mech. Eng. Sci., Vol.11, pp.486-497, 1969')

        # 適用範囲 : 球殻は薄肉であること。

    def Calc(self):
        df = super().GetData()

        l  = df['l']          # crack length
        t  = df['t']          # thickness
        Ri = df['Ri']         # inner radius
        Sy = df['Sy']         # yield stress
        sigma_m = df['sigma_m']  # membrane stress

        lambda_ = l / (2.0 * np.sqrt(Ri * t))
        phi = l / (2.0 * Ri)
        Lr = (sigma_m / Sy) * (1.0 + np.sqrt(1.0 + 8.0 * (lambda_ / np.cos(phi))**2)) / 2.0

        res = {'Lr': Lr}
        super().SetRes(res)
class L_7_b(Base):
    def __init__(self):
        super().SetTitle('片側1/4楕円コーナき裂')
        super().SetRefer('Willoughby, A. A. and Davey, T. G.: ASTM STP 1020, ASTM, Philadelphia, pp.390-409, 1989')

        # 適用範囲: a/t ≦ 0.8, (l + t)/(w - R) ≦ 1.0

    def Calc(self):
        df = super().GetData()

        a = df['a']            # crack depth
        c = df['c']            # crack half length parameter (l = 2c)
        t = df['t']            # thickness
        w = df['w']            # half width
        P = df['P']            # tensile load
        M = df['M']            # bending moment
        Sy = df['Sy']          # yield stress

        sigma_m = P / (2.0 * w * t)
        sigma_bg = 3.0 * M / (w * t ** 2)
        zeta = a * c / (t * (c + t))

        # 局部崩壊
        Lr = (sigma_bg / 3.0 + np.sqrt((sigma_bg**2) / 9.0 + (1.0 - zeta)**2 * sigma_m**2)) / ((1.0 - zeta)**2 * Sy)

        res = {'Lr': Lr}
        super().SetRes(res)