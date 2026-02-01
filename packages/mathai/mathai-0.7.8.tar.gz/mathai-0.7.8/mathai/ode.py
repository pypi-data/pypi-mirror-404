from collections import Counter
from .diff import diff
from .factor import factor, factor2
from .expand import expand
from .base import *
from .fraction import fraction
from .simplify import simplify
import copy
from .inverse import inverse
from .parser import parse


def jjj(lhs, rhs):
    lst = [lhs, rhs]
    for i in range(2):
        if lst[i].name in ["f_mul", "f_add"]:
            
            out = []
            for child in lst[i].children:
                
                if not contain(child, tree_form(f"v_{i}")):
                    out.append(child)
            if out == []:
                continue
            out = TreeNode(lst[i].name, out)
            
            if len(out.children) == 1:
                out = out.children[0]
            out = out.copy_tree()
            if lst[i].name == "f_add":
                lst[i] = lst[i] - out
                lst[1-i] = lst[1-i] - out
            else:
                lst[i] = lst[i] / out
                lst[1-i] = lst[1-i] / out
                
            lst = [simplify(expand(simplify(item))) for item in lst]
    return lst

def kkk(lhs, rhs, depth=3):
    
    lst = jjj(lhs, rhs)
    
    if depth < 0:
        return lst, False
    if not contain(lst[0], tree_form("v_1")) and not contain(lst[1], tree_form("v_0")):
        return lst, True
    orig = copy.deepcopy(lst)
    for i in range(2):
        if lst[i].name in ["f_mul", "f_add"]:
            for child in lst[i].children:
                
                out = child
                if lst[i].name == "f_add":
                    lst[i] = lst[i] - out
                    lst[1-i] = lst[1-i] - out
                else:
                    lst[i] = lst[i] / out
                    lst[1-i] = lst[1-i] / out
                lst = [simplify(item) for item in lst]
                
                output = kkk(lst[0], lst[1], depth-1)
                lst = orig
                if output[1]:
                    return output
    return lst, False

def inversediff(lhs, rhs):
    out = [[tree_form("d_0"), lhs-rhs], False]
    while True:
        out = list(kkk(out[0][0], out[0][1]))
        if out[1]:
            break
        out[0] = [simplify(item) for item in out[0]]
        
    out = out[0]
    return simplify(e0(out[0]-out[1]))

def allocvar():
    return tree_form("v_101")

def epowersplit(eq):
    if eq.name == "f_pow" and eq.children[1].name == "f_add":
        return product([eq.children[0]**child for child in eq.children[1].children])
    return TreeNode(eq.name, [epowersplit(child) for child in eq.children])
def esolve(s):
    if s.name == "f_add" and "f_log" in str_form(s):
        return product([tree_form("s_e")**child for child in s.children]) - tree_form("d_1")
    return TreeNode(s.name, [esolve(child) for child in s.children])
def diffsolve_sep2(eq):
    global tab
    
    s = []
    eq = simplify(expand(eq))
    eq = e1(eq)
    
    def vlor1(eq):
        if contain(eq, tree_form("v_0")) and not contain(eq, tree_form("v_1")):
            return True
        if contain(eq, tree_form("v_1")) and not contain(eq, tree_form("v_0")):
            return True
        return False
    if eq.name == "f_add" and all(vlor1(child) and [str_form(x) for x in factor_generation(copy.deepcopy(child))].count(str_form(tree_form(vlist(child)[0]).fx("dif")))==1 for child in eq.children):
        for child in eq.children:
            v = vlist(child)[0]
            v2 = tree_form(v).fx("dif")
            child = replace(child, v2, tree_form("d_1"))
            child = simplify(child)
            
            
            tmp6 = TreeNode("f_integrate", [child, tree_form(v)])
            s.append(tmp6)
            
            if s[-1] is None:
                return None
        s.append(allocvar())
    else:
        return None
    s = summation(s)
    s = simplify(e0(s))
    
    return groupe(s)
def e0(eq):
    return TreeNode("f_eq", [eq, tree_form("d_0")])
def e1(eq):
    if eq.name == "f_eq":
        eq = eq.children[0]
    return eq
def groupe(eq):
    eq = esolve(eq)
    eq = simplify(eq)
    eq = fraction(eq)
    eq = simplify(eq)
    eq = epowersplit(eq)
    return eq

def diffsolve_sep(eq):
    eq = epowersplit(eq)
    eq = inversediff(tree_form("d_0"), eq.children[0].copy_tree())
    return eq

def diffsolve(eq):
    orig = eq.copy_tree()
    if order(eq) == 2:
        for i in range(2):
            out = second_order_dif(eq, tree_form(f"v_{i}"), tree_form(f"v_{1-i}"))
            if out is not None:
                return out
        return orig
    
    eq = diffsolve_sep2(diffsolve_sep(eq))
    if eq is None:
        for i in range(2):
            a = tree_form(f"v_{i}")
            b = tree_form(f"v_{1-i}")
            c = tree_form("v_2")
            eq2 = replace(orig, b,b*a)
            eq2 = replace(eq2, (a*b).fx("dif"), a.fx("dif")*b + b.fx("dif")*a)
            eq2 = expand(simplify(fraction(simplify(eq2))))
            eq2 = diffsolve_sep(eq2)
            eq2 = diffsolve_sep2(eq2)
            if eq2 is not None:
                return e0(TreeNode("f_subs", [replace(eq2.children[0],b,c), c,b/a]).fx("try"))
        eq = orig
    
    eq = fraction(eq)
    eq = simplify(eq)
    for i in range(2):
        
        out = linear_dif(eq, tree_form(f"v_{i}"), tree_form(f"v_{1-i}"))
        if out is not None:
            return out
    return eq
def clist(x):
    return list(x.elements())
def collect_term(eq, term_lst):
    
    lst = None
    if eq.name == "f_add":
        lst = copy.deepcopy(eq.children)
    else:
        lst = [eq]
        
    other = []
    dic = {}
    term_lst = list(sorted(term_lst, key=lambda x: -len(factor_generation(x))))
    for item in term_lst:
        dic[item] = tree_form("d_0")
    for item2 in lst:
        done = True
        tmp2 = Counter(factor_generation(item2))
        for index, item in enumerate(term_lst):
            
            tmp = Counter(factor_generation(item))
            
            if (tmp2&tmp) == tmp:
                if item in dic.keys():
                    
                    dic[item] += product(clist(tmp2-tmp))
                else:
                    
                    dic[item] = product(clist(tmp2-tmp))
                done = False
                break
        if done:
            other.append(item2)
    other = summation(other)
    
    for key in dic.keys():
        dic[key] = simplify(dic[key])
    return [dic, simplify(other)]
def order(eq,m=0):
    best = m
    if eq.name in ["f_pdif", "f_dif"]:
        out = order(eq.children[0], m+1)
        best = max(out, best)
    else:
        for child in eq.children:
            out = order(child, m)
            best = max(out, best)
    return best
def second_order_dif(eq, a, b):
    eq = simplify(eq)
    nn = [TreeNode("f_dif", [TreeNode("f_dif", [b,a]),a]), TreeNode("f_dif", [b,a]), b]
    out = collect_term(eq.children[0], nn)
    if out[1] == tree_form("d_0"):
        tmp = out[0][nn[0]]
        if tmp != tree_form("d_0"):
            for key in out[0].keys():
                out[0][key] = simplify(out[0][key]/tmp)
                
            B = out[0][nn[1]]
            C = out[0][nn[2]]
            
            if all(all(not contain(item, item2) for item2 in [a,b]) for item in [B, C]):
                r = parse("r")
                s = simplify(factor2(simplify(TreeNode("f_eq", [r**2 + B*r + C, tree_form("d_0")])), True))
                r1, r2 = [inverse(item, r.name) for item in s.children[0].children]
                out = None
                if contain(r1, tree_form("s_i")):
                    real = simplify(fraction((r1+r2)/tree_form("d_2")))
                    imagine = simplify((r1-real)/tree_form("s_i"))
                    out = tree_form("s_e")**(real*a)*(tree_form("v_101")*(imagine*a).fx("cos")+tree_form("v_102")*(imagine*a).fx("sin"))
                elif fraction(simplify(r1-r2)) == tree_form("d_0"):
                    out =(tree_form("v_101")+tree_form("v_102")*a)*tree_form("s_e")**(r1*a)
                else:
                    out = tree_form("v_101")*tree_form("s_e")**(r1*a) + tree_form("v_102")*tree_form("s_e")**(r2*a)
                return TreeNode("f_eq", [b, out])
    return None
                
def linear_dif(eq, a, b):
    eq = simplify(eq)
    
    out = collect_term(eq.children[0], [b.fx("dif"), b*a.fx("dif"), a.fx("dif")])
    
    if out[1] == tree_form("d_0"):
        tmp = out[0][b.fx("dif")]
        if tmp != tree_form("d_0"):
            
            for key in out[0].keys():
                out[0][key] = simplify(out[0][key]/tmp)
            p, q = out[0][b*a.fx("dif")], -out[0][a.fx("dif")]
            
            f = tree_form("s_e") ** TreeNode("f_integrate", [p, a])
            return simplify(TreeNode("f_eq", [b*f, TreeNode("f_integrate", [q*f, a])+allocvar()]))
    return None
