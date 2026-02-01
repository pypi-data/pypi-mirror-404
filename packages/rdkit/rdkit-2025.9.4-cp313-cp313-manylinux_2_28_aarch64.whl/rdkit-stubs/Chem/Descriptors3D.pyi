"""
Descriptors derived from a molecule's 3D structure

"""
from __future__ import annotations
from rdkit.Chem.Descriptors import _isCallable
from rdkit.Chem import rdMolDescriptors
__all__: list[str] = ['CalcMolDescriptors3D', 'descList', 'rdMolDescriptors']
def CalcMolDescriptors3D(mol, confId = -1):
    """
    
    Compute all 3D descriptors of a molecule
    
    Arguments:
    - mol: the molecule to work with
    - confId: conformer ID to work with. If not specified the default (-1) is used
    
    Return:
    
    dict
        A dictionary with decriptor names as keys and the descriptor values as values
    
    raises a ValueError 
        If the molecule does not have conformers
    """
def _setupDescriptors(namespace):
    ...
descList: list  # value = [('PMI1', <function <lambda> at 0xffff95670b80>), ('PMI2', <function <lambda> at 0xffff95670d60>), ('PMI3', <function <lambda> at 0xffff956714e0>), ('NPR1', <function <lambda> at 0xffff95671580>), ('NPR2', <function <lambda> at 0xffff95671620>), ('RadiusOfGyration', <function <lambda> at 0xffff956716c0>), ('InertialShapeFactor', <function <lambda> at 0xffff95671760>), ('Eccentricity', <function <lambda> at 0xffff95671800>), ('Asphericity', <function <lambda> at 0xffff956718a0>), ('SpherocityIndex', <function <lambda> at 0xffff95671940>), ('PBF', <function <lambda> at 0xffff956719e0>)]
