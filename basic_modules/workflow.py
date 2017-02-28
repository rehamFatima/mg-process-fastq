# ------------------------------------------------------------------------------
# Main Workflow interface
# ------------------------------------------------------------------------------
class Workflow(object):
    """
    Abstract class describing a Workflow.

    Workflows are similar to Tools in that they are defined as receiving a
    precise input data type to produce a precise output data type. The main
    difference is that, instead of performing the operations themselves, they
    instantiate other Tools and call their "run()" method to define a flow of
    operations. Workflows can be further nested, to provide easy access to very
    complex pipelines. Furthermore, Workflows automatically take advantage of
    the VRE's ability to optimise the data flow between operations: this is a
    powerful strategy to implement the most data intensive pipelines.

    The Workflow itself is executed by calling its "run()" method; as for
    Tools, "run()" should support multiple inputs and outputs, which are
    assumed to be valid file names locally accessible to the Workflow. This
    allows the Workflow to use the output of Tools as input for other Tools.

    The "run()" method of Workflows should keep track of these intermediate
    outputs by using the "add_intermediate()" method, to allow the wrapping App
    to unstage these (see App).

    As for Tools, Workflows are expected to generate metadata for each of the
    outputs (as well as for intermediate outputs); generally the metadata
    generated by the Tools called by the Workflow will be sufficient.

    """
    input_data_type = None
    output_data_type = None
    intermediate_outputs = []
    configuration = {}

    def add_intermediate(self, output_file, metadata):
        """
        Add an intermediate output file, complete with its metadata. It is the
        App's responsibility to look for these and unstage them: see also
        WorkflowApp.


        Parameters
        ----------
        output_file : str
        	Valid file name locally accessible to the Tool.
        metadata : Metadata
        	Corresponding metadata instance.


        Returns
        -------
        bool
        	True upon success.
        """
        for fname, meta in zip(output_file, metadata):
            self.intermediate_outputs.append((fname, meta))
        return True

    def run(self, input_files, metadata=None):
        """
        Perform the required operations to achieve the functionality of the
        Workflow. This usually involves:
        0. Perform relevant checks on the input
        1. Instantiate a Tool and run it using some input data
        2. Add the Tool's output to the intermediates
        3. Repeat from 1 as many times as required
        4. Optionally edit the output metadata
        5. Return the output files and metadata

        See also help(Tool.run).
        """
        pass
