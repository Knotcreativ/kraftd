/**
 * Type Declarations for Third-Party Libraries
 */

declare module 'react-beautiful-dnd' {
  export interface DraggableProvidedDragHandleProps {
    onMouseDown?: (e: React.MouseEvent<any>) => void;
    onTouchStart?: (e: React.TouchEvent<any>) => void;
    onDragStart?: (e: React.DragEvent<any>) => void;
    draggable?: boolean;
    'data-react-beautiful-dnd-drag-handle__context-id'?: string;
    'aria-roledescription'?: string;
    role?: string;
  }

  export interface DraggableProvidedDraggableProps {
    'data-react-beautiful-dnd-draggable-context-id': string;
    'data-react-beautiful-dnd-draggable-id': string;
  }

  export interface DraggableProvidedDraggableProps {
    onTransitionEnd?: (e: TransitionEvent) => void;
  }

  export interface DraggableProvided {
    innerRef(element?: HTMLElement | null): any;
    draggableProps: DraggableProvidedDraggableProps;
    dragHandleProps: DraggableProvidedDragHandleProps | null;
  }

  export interface DraggableStateSnapshot {
    isDragging: boolean;
    isDropAnimating: boolean;
  }

  export interface DroppableProvidedProps {
    onDragEnter?: (e: React.DragEvent<any>) => void;
    onDragOver?: (e: React.DragEvent<any>) => void;
    onDrop?: (e: React.DragEvent<any>) => void;
  }

  export interface DroppableProvided {
    innerRef(element?: HTMLElement | null): any;
    droppableProps: DroppableProvidedProps;
    placeholder?: React.ReactElement<any>;
  }

  export interface DroppableStateSnapshot {
    isDraggingOver: boolean;
    draggingOverWith?: string;
    draggingFromThisWith?: string;
    isUsingPlaceholder: boolean;
  }

  export interface DropResult {
    reason: 'DROP' | 'CANCEL';
    source: {
      droppableId: string;
      index: number;
    };
    destination?: {
      droppableId: string;
      index: number;
    };
    draggableId: string;
    type: string;
    combine?: {
      draggableId: string;
      droppableId: string;
    };
    mode: 'FLUID' | 'SNAP';
  }

  export function Draggable(props: {
    draggableId: string;
    index: number;
    children: (provided: DraggableProvided, snapshot: DraggableStateSnapshot) => React.ReactElement;
    type?: string;
    isDragDisabled?: boolean;
  }): React.ReactElement;

  export function Droppable(props: {
    droppableId: string;
    children: (provided: DroppableProvided, snapshot: DroppableStateSnapshot) => React.ReactElement;
    type?: string;
    ignoreContainerClipping?: boolean;
    isDropDisabled?: boolean;
    direction?: 'vertical' | 'horizontal';
  }): React.ReactElement;

  export function DragDropContext(props: {
    onDragStart?: (initial: any, provided: any) => void;
    onDragUpdate?: (update: any, provided: any) => void;
    onDragEnd: (result: DropResult, provided: any) => void;
    children: React.ReactNode;
    sensors?: any[];
    enableDefaultSensors?: boolean;
  }): React.ReactElement;
}

declare module 'file-saver' {
  export function saveAs(blob: Blob | File, filename: string): void;
}
