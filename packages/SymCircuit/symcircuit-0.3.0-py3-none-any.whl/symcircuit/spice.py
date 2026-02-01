import warnings
from typing import Tuple, Sequence, List, Dict, Optional, TextIO

import networkx as nx
import sympy
from sympy import Expr, Symbol, Eq


class Element:
    def __init__(self, kind: str, name: str, nodes: Sequence[str], parameters: Sequence[str]) -> None:
        self.name = name
        self.kind = kind
        self.nodes: Sequence[str] = tuple(nodes)
        self.parameters: Sequence[str] = tuple(parameters)

    def __str__(self) -> str:
        return self.name

    def port_connections(self) -> Sequence[Tuple[str, str]]:
        raise NotImplementedError(f"port_connections must be overridden, class: {self.__class__.__name__}")

    def voltage_drop(self, p1: str, p2: str) -> Optional[Expr]:
        pass

    def currents(self, builder: "EquationBuilder"):
        pass

    def sym_variable(self, item: str = "") -> Symbol:
        if item:
            return Symbol(f"{item}_{self.name}")
        return Symbol(self.name)


class PassiveTwoPort(Element):
    def port_connections(self) -> Sequence[Tuple[str, str]]:
        return [(self.nodes[0], self.nodes[1])]

    def get_impedance(self) -> Expr:
        raise NotImplementedError()

    def voltage_drop(self, p1: str, p2: str) -> Expr:
        if (p1, p2) == self.nodes:
            i = self.sym_variable("i")
            return i * self.get_impedance()

    def currents(self, builder: "EquationBuilder"):
        i = self.sym_variable("i")
        builder.add_node_current(self.nodes[0], i, "in")
        builder.add_node_current(self.nodes[1], i, "out")


class Resistor(PassiveTwoPort):
    def __init__(self, name: str, n1: str, n2: str, value: str) -> None:
        super().__init__("R", name, (n1, n2), [value])

    def get_impedance(self) -> Expr:
        return self.sym_variable()


class Capacitor(PassiveTwoPort):
    def __init__(self, name: str, n1: str, n2: str, value: str) -> None:
        super().__init__("C", name, (n1, n2), [value])

    def get_impedance(self) -> Expr:
        X = 1 / (Symbol("s") * self.sym_variable())
        return X


class Inductor(PassiveTwoPort):
    def __init__(self, name: str, n1: str, n2: str, value: str) -> None:
        super().__init__("L", name, (n1, n2), [value])

    def get_impedance(self) -> Expr:
        X = Symbol("s") * self.sym_variable()
        return X


class Voltage(Element):
    def __init__(self, name: str, np: str, nn: str, typ: str, value: str) -> None:
        super().__init__("V", name, (np, nn), (typ, value))

    def port_connections(self) -> Sequence[Tuple[str, str]]:
        return [(self.nodes[0], self.nodes[1])]

    def voltage_drop(self, p1: str, p2: str) -> Optional[Expr]:
        if (p1, p2) == self.nodes:
            return self.sym_variable()

    def currents(self, builder: "EquationBuilder"):
        i = self.sym_variable("i")
        builder.add_node_current(self.nodes[0], i, "in")
        builder.add_node_current(self.nodes[1], i, "out")


class Current(Element):
    def __init__(self, name: str, np: str, nn: str, typ: str, value: str) -> None:
        super().__init__("I", name, (np, nn), (typ, value))

    def port_connections(self) -> Sequence[Tuple[str, str]]:
        return [(self.nodes[0], self.nodes[1])]

    def voltage_drop(self, p1: str, p2: str) -> Optional[Expr]:
        return sympy.sympify("0")

    def currents(self, builder: "EquationBuilder"):
        i = self.sym_variable()
        builder.add_node_current(self.nodes[0], i, "in")
        builder.add_node_current(self.nodes[1], i, "out")


class VirtualShort(Element):

    def __init__(self, name: str, np: str, nn: str) -> None:
        super().__init__("V", name, (np, nn), [])

    def port_connections(self) -> Sequence[Tuple[str, str]]:
        return [(self.nodes[0], self.nodes[1])]

    def voltage_drop(self, p1: str, p2: str) -> Optional[Expr]:
        return sympy.sympify("0")

    def currents(self, builder: "EquationBuilder"):
        i = self.sym_variable("i")
        builder.add_node_current(self.nodes[0], i, "in")
        builder.add_node_current(self.nodes[1], i, "out")


class Diode(Element):
    def __init__(self, name: str, np: str, nn: str, model: str) -> None:
        super().__init__("D", name, (np, nn), (model,))


class Transistor(Element):
    def __init__(self, name: str, nc: str, nb: str, ne: str, ns: str, model: str) -> None:
        super().__init__("Q", name, (nc, nb, ne, ns), (model,))
        warnings.warn("Transistor is not fully implemented")

    def port_connections(self) -> Sequence[Tuple[str, str]]:
        # collector->emitter, base->emitter, base->collector
        return [(self.nodes[0], self.nodes[2]), (self.nodes[1], self.nodes[2]), (self.nodes[1], self.nodes[0])]


class EquationBuilder:

    def __init__(self) -> None:
        self.nodes: Dict[str, List[Expr]] = {}
        self.working_loop: List[Expr] = []

    def negative(self, e: Expr) -> Expr:
        return (-e).simplify()

    def item(self, name: str, item: str) -> Symbol:
        return Symbol(f"{name}_{item}")

    def add_node_current(self, node: str, curr: Symbol, direction="in"):
        if node not in self.nodes:
            self.nodes[node] = []
        if direction == "in":
            self.nodes[node].append(curr)
        elif direction == "out":
            self.nodes[node].append(self.negative(curr))
        else:
            raise ValueError(f"Invalid direction: {direction}")

    def node_equations(self):
        for net, flows in self.nodes.items():
            e = Eq(sum(flows), 0)
            yield e

    def begin_loop(self):
        self.working_loop.clear()

    def finish_loop(self, name: str) -> Expr:
        e = Eq(sum(self.working_loop), 0)
        return e

    def do_voltage(self, element: Element, a: str, b: str):
        vd = element.voltage_drop(a, b)
        if vd is None:
            vd = element.voltage_drop(b, a)
            if vd is not None:
                vd = self.negative(vd)
        if vd is not None:
            self.working_loop.append(vd)
        else:
            warnings.warn(f"No voltage drop defined by {str(element)} from {a} to {b}")


class Circuit:
    def __init__(self) -> None:
        self.elements: List[Element] = []

    def add(self, el: Element):
        self.elements.append(el)

    def parse_spice_netlist(self, source: TextIO):
        def nameof(s: str) -> str:
            try:
                return s[s.index("§") + 1:]
            except ValueError:
                return s

        self.elements.clear()
        for line in source:
            line = line.strip()
            if not line or (line[0] in ("*", ".")):
                continue
            typ = line[0]
            words = line.split()
            if typ == "R":
                self.add(Resistor(nameof(words[0]), *words[1:4]))
            elif typ == "C":
                self.add(Capacitor(nameof(words[0]), *words[1:4]))
            elif typ == "L":
                self.add(Inductor(nameof(words[0]), *words[1:4]))
            elif typ == "V":
                self.add(Voltage(nameof(words[0]), *words[1:5]))
            elif typ == "I":
                self.add(Current(nameof(words[0]), *words[1:5]))
            elif typ == "D":
                self.add(Diode(nameof(words[0]), *words[1:4]))
            elif typ == "Q":
                self.add(Transistor(nameof(words[0]), *words[1:6]))
            else:
                warnings.warn("Unknown SPICE instruction: " + line)

    @staticmethod
    def get_node_alias(G: nx.Graph, fro: str, node: str) -> str:
        j = 0
        while True:
            j += 1
            t = f"{node}#{j}"
            if not G.has_edge(fro, t):
                return t

    @staticmethod
    def strip_node_alias(node: str) -> str:
        try:
            return node[:node.rindex("#")]
        except ValueError:
            return node

    def to_graph(self) -> nx.Graph:
        # In a circuit graph, potentials are nodes, "double nodes" collapse into one network name
        # ciruit elements are edges on the graph
        # elements with more than two ports are responsible for adding themselves correctly later on
        grph = nx.Graph()
        for el in self.elements:
            for i, o in el.port_connections():
                if not grph.has_edge(i, o):
                    grph.add_edge(i, o, element=el)
                else:
                    # no parallel edges allowed in NetworkX Graph, and Multigraph doesn't have well-defined cycle bases
                    # replace one side by fictional node and "fix it in post"
                    t = Circuit.get_node_alias(grph, i, o)
                    grph.add_edge(i, t, element=el)
                    grph.add_edge(o, t, element=VirtualShort(t, i, t))
        return grph

    @staticmethod
    def draw_graph(graph: nx.Graph, ax=None):
        lay = nx.planar_layout(graph)
        nx.draw(graph, pos=lay, edge_color='black', width=1, linewidths=1,
                node_size=500, node_color='pink', alpha=0.9,
                labels={node: node for node in graph.nodes()})
        edges = {}
        for i, o, el in graph.edges(data="element"):
            edges[(i, o)] = str(el)
        nx.draw_networkx_edge_labels(graph, lay, edge_labels=edges)

    @staticmethod
    def graph_to_equations(graph: nx.Graph) -> List[Expr]:
        builder = EquationBuilder()
        connected_elements = set()
        equations = []
        # Kirchhoff's Voltage Law
        all_cycles = nx.cycle_basis(graph, "0")
        for iloop, loop in enumerate(all_cycles):
            builder.begin_loop()
            for a, b in zip(loop, loop[1:] + loop[:1]):
                element = graph.get_edge_data(a, b)["element"]
                if isinstance(element, VirtualShort):
                    continue
                a = Circuit.strip_node_alias(a)
                b = Circuit.strip_node_alias(b)
                builder.do_voltage(element, a, b)
                connected_elements.add(element)
            lopeq = builder.finish_loop(str(iloop))
            equations.append(lopeq)
        # Kirchhoff's Current Law
        for element in sorted(connected_elements, key=lambda el: el.name):
            element.currents(builder)
        for nodeq in builder.node_equations():
            equations.append(nodeq)
        return equations

    def to_system_description(self) -> str:
        g = self.to_graph()
        eqs = Circuit.graph_to_equations(g)
        script = "\n".join(map(str, eqs))
        script += "\ns == const"
        for el in self.elements:
            script += f"\n{el.name} == const"
        return script
