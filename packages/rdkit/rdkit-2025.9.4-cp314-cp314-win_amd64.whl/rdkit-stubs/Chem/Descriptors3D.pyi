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
descList: list  # value = [('PMI1', <function <lambda> at 0x00000261466BBD70>), ('PMI2', <function <lambda> at 0x00000261488603B0>), ('PMI3', <function <lambda> at 0x0000026148860460>), ('NPR1', <function <lambda> at 0x0000026148860510>), ('NPR2', <function <lambda> at 0x00000261488605C0>), ('RadiusOfGyration', <function <lambda> at 0x0000026148860670>), ('InertialShapeFactor', <function <lambda> at 0x0000026148860720>), ('Eccentricity', <function <lambda> at 0x00000261488607D0>), ('Asphericity', <function <lambda> at 0x0000026148860880>), ('SpherocityIndex', <function <lambda> at 0x0000026148860930>), ('PBF', <function <lambda> at 0x00000261488609E0>)]
