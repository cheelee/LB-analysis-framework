###############################################################################
#
#                       lbsStrictLocalizingCriterion.py
#                           DARMA Toolkit v. 1.0.0
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
lbsStrictLocalizingCriterion_module_aliases = {}
for m in [
    "bcolors",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsStrictLocalizingCriterion_module_aliases:
            globals()[lbsStrictLocalizingCriterion_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Execution.lbsCriterionBase   import CriterionBase

###############################################################################
class StrictLocalizingCriterion(CriterionBase):
    """A concrete class for a strictly localizing criterion
    """
    
    ###########################################################################
    def __init__(self, processors, edges, _):
        """Class constructor:
        processors: set of processors (lbsProcessor.Processor instances)
        edges: dictionary of edges (frozensets)
        _: no parameters dictionary needed for this criterion
        """

        # Call superclass init
        super(StrictLocalizingCriterion, self).__init__(processors, edges)
        print(bcolors.HEADER
            + "[StrictLocalizingCriterion] "
            + bcolors.END
            + "Instantiated concrete criterion")

    ###########################################################################
    def compute(self, object, p_src, _):
        """A criterion enforcing strict conservation of local communications
        """

        # Keep track source processsor ID
        p_src_id = p_src.get_id()

        # Retrieve object communications
        comm = object.get_communicator()

        # Iterate over sent messages
        for i in comm.get_sent().items():
            if p_src_id == i[0].get_processor_id():
                # Bail out as soon as locality is broken by transfer
                return -1.

        # Iterate over received messages
        for i in comm.get_received().items():
            if p_src_id == i[0].get_processor_id():
                # Bail out as soon as locality is broken by transfer
                return -1.

        # Criterion returns a positive value meaning acceptance
        return 1.

###############################################################################
