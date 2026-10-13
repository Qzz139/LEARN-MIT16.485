"""Render the live ROS node/topic graph exactly like rqt_graph (Nodes/Topics), without the GUI."""
import inspect, sys
import rosgraph.impl.graph
from rqt_graph.dotcode import RosGraphDotcodeGenerator, NODE_TOPIC_GRAPH
from qt_dotgraph.pydotfactory import PydotFactory

g = rosgraph.impl.graph.Graph()
g.set_master_stale(5.0); g.set_node_stale(5.0); g.update()
gen = RosGraphDotcodeGenerator()
kw = dict(rosgraphinst=g, ns_filter="", topic_filter="", graph_mode=NODE_TOPIC_GRAPH,
          dotcode_factory=PydotFactory(), hide_dead_end_topics=True, quiet=True,
          orientation="LR", hide_dynamic_reconfigure=True)
params = inspect.signature(gen.generate_dotcode).parameters
dot = gen.generate_dotcode(**{k: v for k, v in kw.items() if k in params})
open(sys.argv[1], "w").write(dot)
