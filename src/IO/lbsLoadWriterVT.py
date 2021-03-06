#
#@HEADER
###############################################################################
#
#                              lbsLoadWriterVT.py
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
#@HEADER
#
########################################################################
lbsLoadWriterVT_module_aliases = {}
for m in [
    "bcolors",
    "csv",
    ]:
    has_flag = "has_" + m.replace('.', '_')
    try:
        module_object = __import__(m)
        if m in lbsLoadWriterVT_module_aliases:
            globals()[lbsLoadWriterVT_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("** ERROR: failed to import {}. {}.".format(m, e))
        globals()[has_flag] = False

from Model  import lbsPhase

########################################################################
class LoadWriterVT:
    """A class to write load directives for VT as CSV files with
    the following format:

      <iter/phase>, <object-id>, <time>

    Each file is named as <base-name>.<node>.out, where <node> spans the number
    of MPI ranks that VT is utilizing.

    Each line in a given file specifies the load of each object that must
    be mapped to that VT node for a given iteration/phase.
    """

  ####################################################################
    def __init__(self, e, f="lbs_out", s="vom"):
        """Class constructor:
        e: Phase instance
        f: file name stem
        s: suffix
        """

        # Ensure that provided phase has correct type
        if not isinstance(e, lbsPhase.Phase):
            print(bcolors.ERR
                + "*  ERROR: [LoadWriterExodusII] Could not write to ExodusII file by lack of a LBS phase"
                + bcolors.END)
            return

        # Assign internals
        self.phase = e
        self.file_stem = "{}".format(f)
        self.suffix = s

    ####################################################################
    def write(self, time_step):
        """Write one CSV file per rank/procesor containing with one object
        per line, with the following format:

            <source processor>, <object-id>, <time>
        """

        # Iterate over processors
        for p in self.phase.processors:
            # Create file name for current processor
            file_name = "{}.{}.{}.{}".format(
                self.file_stem,
                time_step,
                p.get_id(),
                self.suffix)
            
            # Count number of unsaved objects for sanity
            n_u = 0

            # Open output file
            with open(file_name, 'w') as f:
                # Create CSV writer
                writer = csv.writer(f, delimiter=',')

                # Iterate over objects
                for o in p.objects:
                    # Write object to file and increment count
                    try:
                        writer.writerow([o.get_processor_id(),
                                         o.get_id(),
                                         o.get_time()])
                    except:
                        n_u += 1

            # Sanity check
            if n_u:
                print(bcolors.ERR
                    + "*  ERROR: {} objects could not be written to CSV file {}".format(
                    n_u,
                    file_name)
                    + bcolors.END)
            else:
                print(bcolors.HEADER
                    + "[LoadWriterVT] "
                    + bcolors.END
                    + "Wrote {} objects to CSV file {}".format(
                    len(p.objects),
                    file_name))

########################################################################
