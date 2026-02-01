"""Defines components of an .fchk file that are already known and parseable"""

# from ...Parsers.RegexPatterns import *
from .FChkDerivatives import *
import numpy as np

########################################################################################################################
#
#                                           FormattedCheckpointComponents
#
#region FormattedCheckpointComponents
FormattedCheckpointComponents = { } # we'll register on this bit by bit
# each registration should look like:

# FormattedCheckpointComponents["Name"] = parser

#endregion

########################################################################################################################
#
#                                          Int Atom Types
#

#region IInt Atom Types

def get_names(atom_ints, reader=None):
    from ...Data import AtomData
    return [ AtomData[x, "Symbol"] for x in atom_ints ]
FormattedCheckpointComponents["Int Atom Types"] = get_names

#endregion

########################################################################################################################
#
#                                          Current cartesian coordinates
#

#region Current cartesian coordinates

def reformat(coords, reader=None):
    import numpy as np

    ncoords = len(coords)
    return np.reshape(coords, (int(ncoords/3), 3))
FormattedCheckpointComponents["Current cartesian coordinates"] = reformat

#endregion

########################################################################################################################
#
#                                           Cartesian Force Constants
#

#region Cartesian Force Constants

FormattedCheckpointComponents["Cartesian Force Constants"] = FchkForceConstants

#endregion

########################################################################################################################
#
#                                           Cartesian 3rd/4th derivatives
#

#region Cartesian 3rd/4th derivatives

FormattedCheckpointComponents["Cartesian 3rd/4th derivatives"] = FchkForceDerivatives

#endregion

########################################################################################################################
#
#                                           Dipole Derivatives
#

#region Dipole Derivatives

FormattedCheckpointComponents["Dipole Derivatives"] = FchkDipoleDerivatives

#endregion

########################################################################################################################
#
#                                           Dipole Derivatives num derivs
#

#region Dipole Derivatives num derivs

FormattedCheckpointComponents["Dipole Moment num derivs"] = FchkDipoleNumDerivatives

#region Dipole Derivatives num derivs

FormattedCheckpointComponents["Dipole Derivatives num derivs"] = FchkDipoleHigherDerivatives

def parse_pol(pol_array, tril=np.tril_indices(3), reader=None):
    full_array = np.zeros((3, 3), dtype=float)
    full_array[tril] = pol_array
    r,c = tril
    full_array[c,r] = pol_array
    return full_array
FormattedCheckpointComponents["Polarizability"] = parse_pol
def parse_hyper_pol(pol_array, tril=np.tril_indices(3), reader=None):
    import itertools
    full_array = np.zeros((3, 3, 3), dtype=float)
    i,j,k = list(itertools.combinations_with_replacement(range(3), 3))
    full_array[i,j,k] = pol_array
    full_array[i,k,j] = pol_array
    full_array[k,i,j] = pol_array
    return full_array
FormattedCheckpointComponents["HyperPolarizability"] = parse_pol
def parse_pol_derivs(pol_array, tril=np.tril_indices(3), reader=None):
    n_modes = len(pol_array) // 6
    full_array = np.zeros((n_modes, 3, 3))
    r, c = tril
    for i, block in enumerate(np.array_split(pol_array, n_modes)):
        full_array[i, r, c] = block
        full_array[i, c, r] = block
    return full_array
FormattedCheckpointComponents["Polarizability Derivatives"] = parse_pol_derivs
def parse_pol_num_derivs(pol_array, tril=np.tril_indices(3), reader=None):
    n_modes = len(pol_array) // 12
    firsts = np.zeros((n_modes, 3, 3))
    second_diag = np.zeros((n_modes, n_modes, 3, 3))
    r, c = tril
    for i,block in enumerate(np.array_split(pol_array, n_modes)):
        firsts[i, r,c] = block[:6]
        firsts[i, c, r] = block[:6]
        second_diag[i, i, r,c] = block[6:]
        second_diag[i, i, c, r] = block[6:]
    return firsts, second_diag
FormattedCheckpointComponents["Polarizability num derivs"] = parse_pol_num_derivs

#endregion

########################################################################################################################
#
#                                           Vib-Modes
#

#region Vib-Modes

def split_vib_modes(mcoeffs, reader=None):
    """Pulls the mode vectors from the coeffs
    There should be 3N-6 modes where each vector is 3N long so N = (1 + sqrt(1 + l/9))

    :param mcoeffs:
    :type mcoeffs:
    :return:
    :rtype:
    """
    import numpy as np

    # l = len(mcoeffs)
    n = reader.num_atoms#int(1 + np.sqrt(1 + l/9))
    return np.reshape(mcoeffs, (-1, 3*n))
FormattedCheckpointComponents["Vib-Modes"] = split_vib_modes

#endregion

########################################################################################################################
#
#                                           Vib-E2
#

#region Vib-E2

def split_vib_e2(e2, reader=None):
    """Pulls the vibrational data out of the file

    :param e2:
    :type e2:
    :return:
    :rtype:
    """

    # l = len(e2)
    # n = 1 + np.sqrt(1 + l/9) # I thought this was the way it was defined but...seems like not exactly
    n = reader.num_atoms
    # if n != int(n):
    #     n = l/14
    #     if n != int(n):
    #         raise ValueError("Gaussian FChk Vib-E2 block malformatted")
    # n = int(n)

    m = 3*n - 6

    freq = e2[:m]
    red_m = e2[m:2*m]
    frc_const = e2[2*m:3*m]
    intense = e2[3*m:4*m]

    return {
        "Frequencies"    : freq,
        "ReducedMasses"  : red_m,
        "ForceConstants" : frc_const,
        "Intensities"    : intense
    }
FormattedCheckpointComponents["Vib-E2"] = split_vib_e2

#endregion


########################################################################################################################
#
#                                           CommonNames
#

#region CommonNames

FormattedCheckpointCommonNames = {
    "Atomic numbers": "AtomicNumbers",
    "Current cartesian coordinates":"Coordinates",
    "Cartesian Gradient": "Gradient",
    "Cartesian Force Constants" : "ForceConstants",
    "Cartesian 3rd/4th derivatives" : "ForceDerivatives",
    "Dipole Moment" : "DipoleMoment",
    "Dipole Derivatives" : "DipoleDerivatives",
    "Dipole Moment num derivs" : "DipoleNumDerivatives",
    "Dipole Derivatives num derivs" : "DipoleHigherDerivatives",
    "Vib-E2" : "VibrationalData",
    "Vib-Modes" : "VibrationalModes",
    "Vib-AtMass" : "VibrationalAtomicMasses",
    "Real atomic weights" : "AtomicMasses"
}

#endregion