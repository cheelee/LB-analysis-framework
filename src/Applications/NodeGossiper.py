#!/usr/bin/env python2.7
########################################################################
NodeGossiper_module_aliases = {}
for m in [
    "os",
    "subprocess",
    "getopt",
    "math",
    "sys",
   ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in NodeGossiper_module_aliases:
            globals()[NodeGossiper_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print "*  WARNING: Failed to import " + m + ". {}.".format(e)
        globals()[has_flag] = False

if __name__ == '__main__':
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from Model     import lbsEpoch
        from Execution import lbsRuntime
        from IO        import lbsLoadWriter, lbsStatistics
    else:
        from ..Model     import lbsEpoch
        from ..Execution import lbsRuntime
        from ..IO        import lbsLoadWriter, lbsStatistics

########################################################################
class ggParameters:
    """A class to describe NodeGossiper parameters
    """

    ####################################################################
    def __init__(self):
        # Do not be verbose by default
        self.verbose = False

        # Number of load-balancing iterations
        self.n_iterations = 1

        # Processors are implicitly mapped to a regular grid
        self.grid_size = [1, 1, 1]

        # Number of task objects
        self.n_objects = 1

        # Object time sampler type and parameters
        self.time_sampler_type = None
        self.time_sampler_parameters = []

        # Size of subset to which objects are initially mapped (0 = all)
        self.n_processors = 0

        # Number of gossiping rounds
        self.n_rounds = 1

        # Fan-out factor for information spreading (gossiping)
        self.fanout = 1

        # Relative overload threshold for load transfer
        self.threshold = 1.

        # Base name for reading VT log files to obtain load distribution
        self.log_file = None

    ####################################################################
    def usage(self):
        """Provide online help
        """

        print "Usage:"
        print "\t [-n <ni>]   number of load-balancing iterations"
        print "\t [-x <npx>]  number of procs in x direction"
        print "\t [-y <npy>]  number of procs in y direction"
        print "\t [-z <npz>]  number of procs in z direction"
        print "\t [-o <no>]   number of objects"
        print "\t [-p <np>]   number of initially used processors"
        print "\t [-k <nr>]   number of gossiping rounds"
        print "\t [-f <fo>]   gossiping fan-out value"
        print "\t [-t <rt>]   overload relative threshold"
        print "\t [-s <st>]   time sampler (uniform or lognormal)"
        print "\t [-l <base>] base file name for reading VT load log files"
        print "\t [-v]        make standard output more verbose"
        print "\t [-h]        help: print this message and exit"

    ####################################################################
    def parse_command_line(self):
        """Parse command line and fill grid gossiper parameters
        """

        # Try to hash command line with respect to allowable flags
        try:
            opts, args = getopt.getopt(sys.argv[1:], "f:hk:n:o:p:s:t:vx:y:z:l:")
        except getopt.GetoptError:
            print "** ERROR: incorrect command line arguments."
            self.usage()
            return True

        # Parse arguments and assign corresponding member variable values
        for o, a in opts:
            try:
                i = int(a)
            except:
                i = None
            if o == "-h":
                self.usage()
                return
            elif o == "-v":
                self.verbose = True
            elif o == "-n":
                if i > 0:
                    self.n_iterations = i
            elif o == "-x":
                if i > 0:
                    self.grid_size[0] = i
            elif o == "-y":
                if i > 0:
                    self.grid_size[1] = i
            elif o == "-z":
                if i > 0:
                    self.grid_size[2] = i
            elif o == "-o":
                if i > 0:
                    self.n_objects = i
            elif o == "-p":
                if i > 0:
                    self.n_processors = i
            elif o == "-s":
                a_s = a.split(",")
                if len(a_s):
                    self.time_sampler_type = a_s[0].lower()
                    for p in a_s[1:]:
                        try:
                            self.time_sampler_parameters.append(float(p))
                        except:
                            pass
            elif o == "-k":
                if i > 0:
                    self.n_rounds = i
            elif o == "-f":
                if i > 0:
                    self.fanout = i
            elif o == "-t":
                x = float(a)
                if x > 1.:
                    self.threshold = x
            elif o == "-l":
                self.log_file = a

	# Ensure that exactly one population strategy was chosen
        if (not (self.log_file or self.time_sampler_type)
            or (self.log_file and self.time_sampler_type)):
            print "** ERROR: exactly one strategy to populate initial epoch must be chosen."
            self.usage()
            return True

	# No line parsing error occurred
        return False

########################################################################
def global_id_to_cartesian(id, grid_sizes):
    """Map global index to its Cartesian coordinates in a grid
    """

    # Sanity check
    n01 = grid_sizes[0] * grid_sizes[1]
    if id < 0  or id >= n01 * grid_sizes[2]:
        return None

    # Compute successive euclidean divisions
    k, r = divmod(id, n01)
    j, i = divmod(r, grid_sizes[0])

    # Return Cartesian coordinates
    return i, j, k

########################################################################
if __name__ == '__main__':

    # Print startup information
    sv = sys.version_info
    print "[NodeGossiper] ### Started with Python {}.{}.{}".format(
        sv.major,
        sv.minor,
        sv.micro)

    # Instantiate parameters and set values from command line arguments
    print "[NodeGossiper] Parsing command line arguments"
    params = ggParameters()
    if params.parse_command_line():
       sys.exit(1)

    # Keep track of total number of procs
    n_p = params.grid_size[0] * params.grid_size[1] * params.grid_size[2]
    if n_p < 2:
        print "** ERROR: Total number of processors ({}) must be > 1".format(n_p)
        sys.exit(1)

    # Initialize random number generator
    lbsStatistics.initialize()

    # Create an epoch and populate it
    epoch = lbsEpoch.Epoch()
    if params.log_file:
        # Populate epoch from log files and store number of objects
        n_o = epoch.populate_from_log(n_p, params.log_file)

    else:
        # Create requested pseud-ramdom sampler
        if params.time_sampler_type not in (
            "uniform",
            "lognormal"):
            print "** ERROR: unsupported sampler type: {}".format(
                params.time_sampler_type)
            sys.exit(1)
        if len(params.time_sampler_parameters) != 2:
            print "** ERROR: not enough parameters for sampler type: {}".format(
                params.time_sampler_type)
            sys.exit(1)

        # Populate epoch pseudo-randomly
        epoch.populate_from_sampler(params.n_objects,
                                    params.time_sampler_type,
                                    params.time_sampler_parameters,
                                    n_p,
                                    params.n_processors)

        # Keep track of number of objects
        n_o = params.n_objects

    # Compute and print initial load statistics
    lbsStatistics.print_function_statistics(
        epoch.processors,
        lambda x: x.get_load(),
        "initial processor loads",
        params.verbose)

    # Instantiate runtime
    rt = lbsRuntime.Runtime(epoch, params.verbose)
    rt.execute(params.n_iterations,
               params.n_rounds,
               params.fanout,
               params.threshold)

    # Create mapping from processor to Cartesian grid
    print "[NodeGossiper] Mapping {} processors onto a {}x{}x{} rectilinear grid".format(
        n_p,
        *params.grid_size)
    grid_map = lambda x: global_id_to_cartesian(x.get_id(), params.grid_size)

    # Create output name based on epoch population strategy
    if params.log_file:
        output_name = "NodeGossiper-n{}-l{}-i{}-k{}-f{}-t{}.e".format(
            n_p,
            os.path.basename(params.log_file),
            params.n_iterations,
            params.n_rounds,
            params.fanout,
            "{}".format(params.threshold).replace('.', '_'))
    else:
        output_name = "NodeGossiper-n{}-p{}-o{}-s{}-i{}-k{}-f{}-t{}.e".format(
            n_p,
            params.n_processors,
            params.n_objects,
            params.time_sampler_type,
            params.n_iterations,
            params.n_rounds,
            params.fanout,
            "{}".format(params.threshold).replace('.', '_'))

    # Instantiate epoch to ExodusII file writer
    writer = lbsLoadWriter.LoadWriter(epoch, grid_map, output_name)
    writer.write(rt.statistics,
                 rt.load_distributions)

    # Compute and print final load statistics
    _, _, l_ave, l_max, _, _, _ = lbsStatistics.print_function_statistics(
        epoch.processors,
        lambda x: x.get_load(),
        "final processor loads",
        params.verbose)
    print "\t imbalance = {:.6g}".format(
        l_max / l_ave - 1.)

    # Report on optimal statistics
    q, r = divmod(n_o, n_p)
    ell = n_p * l_ave / n_o
    print "[NodeGossiper] Optimal load statistics for {} objects with all times = {:.6g}".format(
        n_o,
        ell)
    print "\t minimum = {:.6g}  maximum = {:.6g}".format(
        q * ell,
        (q + (1 if r else 0)) * ell)
    print "\t standard deviation = {:.6g}".format(
        ell * math.sqrt(r * (n_p - r)) / n_p)
    print "\t imbalance = {:.6g}".format(
        (n_p - r) / float(n_o) if r else 0.)

    # If this point is reached everything went fine
    print "[NodeGossiper] Process complete ###"

########################################################################
