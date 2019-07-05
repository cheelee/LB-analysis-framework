########################################################################
lbsEpoch_module_aliases = {
    "random": "rnd",
    }
for m in [
    "sys",
    "random",
    ]:
    has_flag = "has_" + m
    try:
        module_object = __import__(m)
        if m in lbsEpoch_module_aliases:
            globals()[lbsEpoch_module_aliases[m]] = module_object
        else:
            globals()[m] = module_object
        globals()[has_flag] = True
    except ImportError as e:
        print("*  WARNING: Failed to import " + m + ". {}.".format(e))
        globals()[has_flag] = False

from Model import lbsObject, lbsProcessor, lbsObjectCommunicator
from IO    import lbsStatistics, lbsLoadReaderVT

########################################################################
class Epoch:
    """A class representing the state of collection of processors with
    objects at a given round
    """

    ####################################################################
    def __init__(self, t=0, verbose=False):
        # Initialize empty list of processors
        self.processors = []

        # Default time-step/phase of this epoch
        self.time_step = t

        # Initialize gossiping round
        self.round_index = 0

        # Enable or disable verbose mode
        self.verbose = verbose

    ####################################################################
    def get_processors_ids(self):
        """Retrieve IDs of processors belonging to epoch
        """

        return [p.get_id() for p in self.processors]

    ####################################################################
    def get_time_step(self):
        """Retrieve the time-step/phase for this epoch
        """

        return self.time_step

    ####################################################################
    def populate_from_samplers(self, n_o, ts, ts_params, c_degree, cs, cs_params, n_p, s_s=0):
        """Use samplers to populate either all or n procs in an epoch
        """

        # Retrieve desired time sampler with its theoretical average
        time_sampler, sampler_name = lbsStatistics.sampler(
            ts,
            ts_params)

        # Create n_o objects with uniformly distributed times in given range
        print("[Epoch] Creating {} objects with times sampled from {}".format(
            n_o,
            sampler_name))
        objects = set([lbsObject.Object(
            i,
            time_sampler()
            ) for i in range(n_o)])

        # Compute and report object time statistics
        lbsStatistics.print_function_statistics(objects,
                                                lambda x: x.get_time(),
                                                "object times")

        # Decide whether communications must be created
        if c_degree > 0:
            # Instantiante communication samplers with requested properties
            weight_sampler, weight_sampler_name = lbsStatistics.sampler(
                cs,
                cs_params)
            p_b = .5
            degree_sampler, degree_sampler_name = lbsStatistics.sampler(
                "binomial",
                [c_degree / p_b, p_b])
            print("[Epoch] Creating communications with weights sampled from {} and sent per objects from {}".format(
                degree_sampler_name,
                weight_sampler_name))

            # Create communicator for each object with only sent communications
            for obj in objects:
                # Draw degree from sampler and cap it
                degree = degree_sampler()
                if degree > n_o - 1:
                    degree = n_o - 1

                # Create object communicator witj outgoing messages
                obj.set_communicator(lbsObjectCommunicator.ObjectCommunicator(
                    {},
                    {o: weight_sampler()
                     for o in rnd.sample(
                         objects.difference([obj]),
                         degree)
                     },
                    obj.get_id()))

            # Create symmetric received communications
            for obj in objects:
                for k, v in obj.get_communicator().get_sent().items():
                    k.get_communicator().get_received()[obj] = v

        # Iterate over all object communicators to valid global communication graph
        w_sent, w_recv = [], []
        for obj in objects:
            i = obj.get_id()
            if self.verbose:
                print("\tobject {}:".format(i))

            # Retrieve communicator and proceed to next object if empty
            comm = obj.get_communicator()
            if not comm:
                if self.verbose:
                    print("\t  None")
                continue

            # Check and summarize communications and update global counters
            w_out, w_in = comm.summarize('\t' if self.verbose else None)
            w_sent += w_out
            w_recv += w_in

        # Perform sanity checks
        if len(w_recv) != len(w_sent):
            print("** ERROR: number of sent and received communications differ: {} <> {}".format(
                len(n_sent),
                len(n_recv)))
            sys.exit(1)

        # Compute and report communication weight statistics
        lbsStatistics.print_function_statistics(w_sent,
                                                lambda x: x,
                                                "communication weights")

        # Create n_p processors
        self.processors = [lbsProcessor.Processor(i) for i in range(n_p)]

        # Randomly assign objects to processors
        if s_s and s_s <= n_p:
            print("[Epoch] Randomly assigning objects to {} processors amongst {}".format(
                s_s,
                n_p))
        else:
            # Sanity check
            if s_s > n_p:
                print("*  WARNING: too many processors ({}) requested: only {} available.".format(
                    s_s,
                    n_p))
                s_s = n_p
            print("[Epoch] Randomly assigning objects to {} processors".format(n_p))
        if s_s > 0:
            # Randomly assign objects to a subset o processors of size s_s
            proc_list = rnd.sample(self.processors, s_s)
            for o in objects:
                p = rnd.choice(proc_list)
                p.add_object(o)
                o.first = p.get_id()
        else:
            # Randomly assign objects to all processors
            for o in objects:
                p = rnd.choice(self.processors)
                p.add_object(o)
                o.first = p.get_id()

    ####################################################################
    def populate_from_log(self, n_p, t_s, basename):
        """Populate this epoch by reading in a load profile from log files
        """

        # Instantiate VT load reader
        reader = lbsLoadReaderVT.LoadReader(basename)

        # Populate epoch with reader output
        print("[Epoch] Reading objects from time-step {} of VOM files with prefix {}".format(
            t_s,
            basename))
        self.processors = reader.read_iteration(n_p, t_s)
        
        # Compute and report object statistics
        objects = set()
        for p in self.processors:
            objects = objects.union(p.objects)
        lbsStatistics.print_function_statistics(objects,
                                                lambda x: x.get_time(),
                                                "object times")
        # Return number of found objects
        return len(objects)

########################################################################
