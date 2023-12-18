import { Coordinate } from "./coordinate";
import { Model } from "../../model";
import type * as p from "../../core/properties";
export declare const ImplicitTarget: import("../../core/kinds").Kinds.Enum<"canvas" | "parent" | "plot" | "frame">;
export type ImplicitTarget = typeof ImplicitTarget["__type__"];
export declare const NodeTarget: import("../../core/kinds").Kinds.Or<[Model, "canvas" | "parent" | "plot" | "frame"]>;
export type NodeTarget = typeof NodeTarget["__type__"];
export declare namespace Node {
    type Attrs = p.AttrsOf<Props>;
    type Props = Coordinate.Props & {
        target: p.Property<NodeTarget>;
        symbol: p.Property<string>;
        offset: p.Property<number>;
    };
}
export interface Node extends Node.Attrs {
}
export declare class Node extends Coordinate {
    properties: Node.Props;
    constructor(attrs?: Partial<Node.Attrs>);
}
export declare const frame_left: Node;
export declare const frame_right: Node;
export declare const frame_top: Node;
export declare const frame_bottom: Node;
//# sourceMappingURL=node.d.ts.map