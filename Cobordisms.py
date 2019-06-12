from itertools import product
import itertools as itertools
import numpy as np
import math
from KhT import *
from Tangles import *

def clt_front_pairs(components):
    """the tangle at the front, in TEI pair notation, of a cobordism with components 'components'."""
    return [component[i:i+2] for component in components for i in range(0,len(component),2)]

def clt_back_pairs(components):
    """the tangle at the back, in TEI pair notation, of a cobordism with components 'components'."""
    return [(component+component[0:1])[i+1:i+3] for component in components for i in range(0,len(component),2)]

def clt_front_arcs(components):
    """the tangle at the front, in TEI arc notation, of a cobordism with components 'components'."""
    return arc_to_involution(clt_front_pairs(components))

def clt_back_arcs(components):
    """the tangle at the back, in TEI arc notation, of a cobordism with components 'components'."""
    return arc_to_involution(clt_back_pairs(components))

class Cobordism(object):
    """A cobordism from a crossingless tangle clt1=front to another clt2=back consists of 
    - clt1=front, (these may just be pointers?)
    - clt2=back, (these may just be pointers?)
    - components (alternative to clt1 and clt2)
    - a list decos of (row) vectors v_i in a numpy array of decorations (decos) of the form [Hpower,dot1,...,dotn,coeff]:
        - the first entry Hpower is a non-negative integer which records the pwer of H
        - the entries dot<i> specify the number of dots (0 or 1) on the ith component. 
            The components are ordered such that each component starts with the lowest index appearing in that component
            and all components are ordered by that first entry. 
        - the last entry coeff is some non-zero integer (= coefficient in the base ring/field)
    """
    def __init__(self,clt1,clt2,decos,comps="default"):
        self.front = clt1
        self.back = clt2
        if comps=="default":
            self.comps = components(clt1,clt2)
        else:
            self.comps = comps
        self.decos = decos
    
    def __add__(self, other):
        if self.decos == []: # Adding the zero cobordism
            return other
        if other.decos == []: # Adding the zero cobordism
            return self
        if self.front!=other.front or self.back!=other.back:# incompatible cobordisms
            raise Exception('The cobordisms {}'.format(self)+' and {}'.format(other)+' are not compatible, because they do not belong to the same morphism space.')
        return Cobordism(self.front,self.back,simplify_decos(self.decos+other.decos),self.comps)


    def __mul__(self, other):
        
        def partition_dC(dC,arcs):
            """find the finest partition of dC that is preserved by arcs. The output is a list of list of indices."""
            partition=[]
            # remaining components in our iteration
            remaining=list(range(len(dC)))
            while len(remaining)>0:
                # pick the first of the remaining components as the nucleus of a new element of dC and remove from remaining
                nucleus = [remaining.pop(0)]
                # list of TEIs of nucleus
                nucleusL = dC[nucleus[0]]
                # find all TEIs of nucleus which arcs connects to a different component (which has to be in the set of remaining components)
                joins = [i for i in nucleusL if arcs[i] not in nucleusL]
                while len(joins)>0:
                    # for the first element of joins, find the component and remove it from the remaining components (strictly reducing len(remaining))
                    new=remaining.pop(find_first_index(remaining,lambda s: arcs[joins[0]] in dC[s]))
                    # add this component to the nucleus of the new element of dC 
                    nucleus.append(new) 
                    # record the TEIs of the component
                    nucleusL=nucleusL+dC[new]
                    # add the new TEIs to joins if arcs sends them outside the nucleus
                    joins=[i for i in joins if arcs[i] not in nucleusL]
                partition.append(nucleus)
            return partition
        
        if self.decos == [] or other.decos == []: #Multiplying by the zero cobordism
            return ZeroCob
        x=self.front
        y=self.back
        z=other.back
        if y!=other.front: # incomposable cobordisms
            raise Exception('The cobordisms {}'.format(self)+' and {}'.format(other)+' are not composable; the first ends on {}'.format(y)+' are not composable; the first ends on {}'.format(other.clt1))
        #components of the fully simplified cobordism from x to z, ordered according to their smallest TEI
        dC=components(x,z)
        comps1=self.comps
        comps2=other.comps

        #finding the boundary component of each c of C
        C=partition_dC(dC,y.arcs)# as lists dc of indices of components
        #print("dC=",dC)
        #print("C=",C)
        
        def find_comp(comp):
            return comp in C
        
        comp1_indices=[[j for j,comp in enumerate(comps1) if comp[0] in dc] for dc in dC]
        comp2_indices=[[j for j,comp in enumerate(comps2) if comp[0] in dc] for dc in dC]
        #print("comp1_indices=",comp1_indices)
        #print("comp2_indices=",comp2_indices)
        
        # |C_i intersect c|
        def c_i_cap_c(c_i,c_flat):
            #return sum(map(lambda s: s in c_flat, c_i))
            return sum([1 for i in c_i if i[0] in c_flat])
        genus=[1-int(0.5*(c_i_cap_c(self.comps,flatten([dC[j] for j in c]))\
                         +c_i_cap_c(other.comps,flatten([dC[j] for j in c]))\
                         -0.5*len(flatten([dC[j] for j in c]))\
                         +len(c))) for c in C]
        
        def decos_from_c(g,r,IdcI):
            if r>0:# r>0 and v_c=1
                return [[g+r-1]+[1 for j in range(IdcI)]+[1]]
            else:
                if g%2==0:# genus even
                    return [[g+IdcI-sum(dots)-1]+list(dots)+[(-1)**(g+IdcI-sum(dots)-1)]\
                            for dots in list(product([0,1], repeat=IdcI))[:-1]]
                if g%2==1:# genus odd
                    return [[g+IdcI-sum(dots)-1]+list(dots)+[((-1)**(g+IdcI-sum(dots)-1))]\
                            for dots in list(product([0,1], repeat=IdcI))[:-1]]\
                            +[[g-1]+[1 for i in range(IdcI)]+[2]]
        
        def combine_decos(l,Hpower,coeff):
            #print(l)
            return [sum([Hpower]+[i[0] for i in l])]+flatten([i[1:-1] for i in l])+[coeff*np.prod([i[-1] for i in l])]
        
        #print("dC = ",dC)
        decos=[]
        for e1 in self.decos:
            for e2 in other.decos:
                partial_decos=[]
                for i,c in enumerate(C):
                    r=sum([e1[index+1] for index in comp1_indices[i]]+[e2[index+1] for index in comp2_indices[i]])# number of dots on c
                    g=genus[i]# genus of the closure of c
                    IdcI=len(c)# number of boundary components of c
                    #print(",g=",g,",IdcI=",IdcI,",e1=",e1,",e2=",e2,",r=",r,",comp1_indices[i]=",comp1_indices[i],",comp2_indices[i]=",comp2_indices[i])
                    partial_decos.append(decos_from_c(g,r,IdcI))   
                    #print([decos_from_c(g,r,IdcI)])
                # decos_from_pair (e1,e2)
                #print("partial_decos = ",partial_decos)
                decos+=[combine_decos(l,e1[0]+e2[0],e1[-1]*e2[-1]) for l in itertools.product(*partial_decos)]
        
        #print("decos = ",decos)
        # reorder the dots according to the order of the components
        #def reorder_dots(order):
        #    return [0]+[i[1]+1 for i in sorted(list(zip(order,range(len(order)))))]+[len(order)+1]
        # final result
        #print("simplify_decos(decos)",simplify_decos(decos))
        #print("C",C)
        #print("flatten(C)",flatten(C))
        #print("reorder_dots(flatten(C))",reorder_dots(flatten(C)))
        # PREVIOUSLY: return Cobordism(x,z,simplify_decos(decos)[:,reorder_dots(flatten(C))])
        #print('reorder dots')
        #print(reorder_dots(flatten(C)))
        #print(simplify_decos(decos))
        #Output = Cobordism(x,z,[[deco[index] for index in reorder_dots(flatten(C))] for deco in simplify_decos(decos)])
        Output = Cobordism(x,z,simplify_decos(decos),[dC[index] for index in flatten(C)])
        Output.ReduceDecorations() # This kills any cobordism in the linear combination that has a dot on the same component as the basepoint
        return Output
    # def __rmul__(self, other):
        # #print('__rmul__')
        # return other
    
    
    def deg(self):
        return len(self.dots)-self.front.total-2*self.Hpower-2*sum(self.dots)
    
    def check(self):
        if self.front.top==self.back.top and self.front.bot==self.back.bot:
            x=components(self.front,self.back)
            return len(x)==len(self.dots) and x==self.comps
        else:
            return False
        
    #def deg_safe(self):
        # check all summands in this linear combination to make sure the element is homogeneous.
        # FIXME
    
    # self is a linear combination of cobordisms, with each cobordism being a different list in decos.
    # ReduceDecorations sets a cobordism, decoration, with a dot on the top 0-th tangle end 
    # (which is chosen to be the basepoint of the cobordism) to be the zero cobordism, by removing decoration from decos
    # This also returns the resulting decorations
    def ReduceDecorations(self):
        ReducedDecorations = [decoration for decoration in self.decos if decoration[1] == 0]
        self.decos = ReducedDecorations
        return ReducedDecorations
    
def simplify_decos(decos):# ToDo: rewrite this without numpy
    if decos == []:
        return []
    decos=np.array(sorted(decos))
    """simplify decos by adding all coeffients of the same decoration, omitting those with coefficient 0."""
    # compute unique Hdots (unique_Hdot[0]) and how often each appears (unique_Hdot[1])
    unique_Hdot=np.unique(decos[:,:-1],return_counts=True,axis=0)
    # add all coefficients; we are assuming here that decos is ordered, otherwise it will not work!
    new_coeffs=[[sum(i)] for i in np.split(decos[:,-1],np.cumsum(unique_Hdot[1])[:-1])]
    # compute new decos
    decos=np.append(unique_Hdot[0],new_coeffs,axis=1)
    # return only those decorations whose coefficient is non-zero
    return (decos[decos[:,-1]!=0,:]).tolist()
    #return [x for x in [add_coeffs(list(g)) for k, g in groupby(sorted(decos),key = lambda s: s[0])] if x[1]!=0]

CLTA = CLT(1,1, [1,0], [0,0])
ZeroCob = Cobordism(CLTA,CLTA,[])