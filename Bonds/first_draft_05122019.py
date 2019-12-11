#### 1 init ###########################################################################################################
import pandas as pd
import numpy as np
import datetime
import math
import matplotlib.pyplot as plt

%matplotlib inline

#assumed as spot rates
us_fed=pd.read_csv("rates1.csv",index_col='years')

#assume volatility
vol=.15

#calculate forward rate
def forward(a=1,b=1):
    fr=(us_fed.loc[a+b]**(a+b)/us_fed.loc[a]**a)** (1/b)
    #fr retuens pd.series ...fr.values returns np.array..[0] retruns value
    return fr.values[0]

#forward curve
def forward_curve(a=1):
    b=1
    #adding zeros to forward curves to match the length of spot-->to add in df
    f1=[0]*a
    while b<=len(us_fed)-a:
        #c=(us_fed.loc[a+b]**(a+b)/us_fed.loc[a]**a)** (1/b)
        c=forward(a,b)
        f1.append(c)
        b+=1
    return f1


#### 2 Bond object ##############################################################################################################
class bond():
    """fv=100,coup=1,mat=1,z=0,price=0,freq fixed to annual payment"""
    def __init__ (self,fv=100,coup=1,mat=1,z=0,price=0):
        self.fv=fv
        self.coup=coup
        self.mat=mat
        self.z=z
                
    def PV_bnd(self):
        b=1
        c=0
        while b<=self.mat:
            if b<self.mat:
                # coup / (1+spot @self.mat) ^ self.mat
                c1=self.coup/((1+us_fed.loc[b]/100)**b)
                c=c+c1
            else:
                #final coup + pri
                c1=(100+self.coup)/((1+us_fed.loc[b]/100)**b)
                c=c+c1
            b+=1
        return c.values[0]

#testing
#b1=bond(coup=.5, mat=4)
#b1.PV_bnd()
    
        


#### 3 making tree frame and initializing it ###########################################################################################

def tree_frame(mat):
    #making framework
    z=[]
    for n in range (1,mat+1):
        z.append([0]*n)
    #z now has the pyramid structure

    #z[0] =spot rate for one period
    z[0]=[us_fed.loc[1].values[0]]

    # creating f(n,1 & Z[n][0]) - finding the topmost rate

    #first forward = spot
    f=[us_fed.loc[1].values[0]]

    for n in range (1,mat):
        fr=forward(n,1)
        #using approximation instead of exp(sigma)
        z[n][0]=fr+ n*(fr*vol)
        f.append(fr)

    #will use the below for testing
    # comment this #
    z[0]=[1]
    fr_test=[1,1.4,1.35,1.86]
    f=fr_test

    for n in range (1,mat):
        z[n][0]=f[n]+ n*(f[n]*vol)
    # comment this #
    
    return (z,f)

#filling up the rates for all the nodes
def tree_val(z,f):
    for n in range (1,len(z)):
        for n1 in range (1,len(z[n])):
            z[n][n1]=z[n][n1-1]- 2*(f[n]*vol)
    return z

#to test, use => 
#tf_z,tf_f=tree_frame(4)
#tree_val(tf_z,tf_f)



#### 4 caliberation iterations for frame ###########################################################################################################

def pv_cal(mat,coup,z):
    pv=[]
    #pv box structure
    for n in range (1,mat+1):
        pv.append([0]*n)

    #last set of payment has pri 100
    pv.append([100]*(mat+1))
    
    #backward induction
    for n in range (mat-1,-1,-1):
        for m in range (0,len(pv[n])):
            pv[n][m]=0.5*((pv[n+1][m]+coup)/(1+z[n][m]/100) +(pv[n+1][m+1]+coup)/(1+z[n][m]/100) )
    
    return pv[0][0]

#chnge the node values
def z_iter(z,mat,f):
    for n in range (1,len(z[mat-1])):
        z[mat-1][n]=z[mat-1][n-1]- 2*(f[n]*vol)
        
def cal(bond,tf_f,z1):
    b1=bond
    margin=.000000001
    it=1

    #initializing dell
    dell=abs(100-pv_cal(b1.mat,b1.coup,z1))/2
    c=0
    c_old=pv_cal(b1.mat,b1.coup,z1)
    # iterating to 500 to avoid infinite loop
    while (it <500):
        #find Pv
        c=pv_cal(b1.mat,b1.coup,z1)
        if ((c >= 100-margin) & (c <= 100+margin)):
            break
        #below loop will keep c below 100
        elif ((c > 100) & (c_old <=100)):
            dell-=dell/2
            z1[b1.mat-1][0]+=dell
            z_iter(z1,b1.mat,tf_f)
        elif (c < 100):
            #dec disc rate if pv <100
            z1[b1.mat-1][0]-=dell
            z_iter(z1,b1.mat,tf_f)
            c_old=c
        elif (c > 100):
            # inc disc rate if pv >100

            z1[b1.mat-1][0]+=dell
            c_old=c
            z_iter(z1,b1.mat,tf_f)

        #print (z1[b1.mat-1],c,c_old,dell)
        it+=1
    return z1

def node_cal (bond_list,tf_f,z1):
    for n in bond_list:
        cal (n,tf_f,z1)
    return z1




#### main ###########################################################################################################

#inputs
#Bonds for caliberation
b2=bond(coup=1.2, mat=2)
b3=bond(coup=1.25, mat=3)
b4=bond(coup=1.4, mat=4)
b_list =[b2,b3,b4]
#bond to price:
bx=bond(coup=1.9, mat=3)
#input done
#b1.PV_bnd()

# the initial rate matrix ->z
tf_z,tf_f=tree_frame(4)
z=tree_val(tf_z,tf_f)

#test to check pv_cal
#pv_2=pv_cal(b1.mat,b1.coup,z)

#to check fn cal
#cal(b1,tf_f,z1)

# to caliberate the tree
z_cal=node_cal (b_list,tf_f,z)
print ( "caliberated nodes={}".format(z_cal))
#TO price a new bond
price=pv_cal(bx.mat,bx.coup,z_cal)
print("")
print("price of bond={}".format(price))
