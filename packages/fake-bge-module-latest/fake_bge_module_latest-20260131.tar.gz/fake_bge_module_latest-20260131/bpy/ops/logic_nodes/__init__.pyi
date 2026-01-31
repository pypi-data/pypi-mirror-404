import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

def add_component(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    component: str | None = "",
) -> None:
    """Add a python Component to the selected object

    :param component: Component Name, Add this Component to the current object
    """

def add_game_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Adds a property available to the UPBGE"""

def add_global_category(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Add a global value category"""

def add_global_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Add a value accessible from anywhere"""

def add_logic_tree_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Adds a property available to the UPBGE"""

def add_portal_in(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    portal_name: str = "Portal",
    mode: typing.Literal[
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"
    ]
    | None = "1",
) -> None:
    """Create a new portal

    :param portal_name: Portal Name
    :param mode: Socket Type
    """

def add_portal_out(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    portal_name: str = "",
) -> None:
    """Create a new portal

    :param portal_name: Portal Name
    """

def add_socket(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    socket_type: str = "NLListItemSocket",
) -> None:
    """Add a socket to this node

    :param socket_type: socket_type
    """

def add_template(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    nl_template_name: str = "",
    owner: str = "",
) -> None:
    """Add a template

    :param nl_template_name: nl_template_name
    :param owner: owner
    """

def apply_logic_tree(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    owner: str = "",
) -> None:
    """Apply the current tree to the selected objects.

    :param owner: owner
    """

def audio_system(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Select the object this tree is applied to"""

def custom_mainloop(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Use a custom Mainloop for this scene"""

def custom_mainloop_tree(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Use a custom Mainloop for this scene"""

def custom_node_templates(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Load Custom Logic Node Templates"""

def edit_custom_node(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Edit Custom Logic Node

    :param index: index
    """

def find_logic_tree(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    tree_name: str = "",
) -> None:
    """Edit

    :param tree_name: tree_name
    """

def generate_code(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    uplogic_installed: bool | None = False,
) -> None:
    """Force generation of code, needed only after updating or if encountering issues

    :param uplogic_installed: uplogic_installed
    """

def generate_project(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Generate basic structure for a new project"""

def get_owner(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    applied_object: str = "",
) -> None:
    """Select the object this tree is applied to

    :param applied_object: applied_object
    """

def install_pyfmodex(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """NOTE: This may take a few seconds and requires internet connection."""

def install_upbge_stubs(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Downloads the latest version of the upbge-stubs module to support autocomplet in your IDE.NOTE: This may take a few seconds and requires internet connection."""

def install_uplogic(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Downloads the latest version of the uplogic module required for running logic nodes.NOTE: This may take a few seconds and requires internet connection."""

def key_selector(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    keycode: str = "",
    is_socket: bool | None = True,
) -> None:
    """Undocumented, consider contributing.

    :param keycode: keycode
    :param is_socket: is_socket
    """

def load_font(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.ttf;*.otf;",
) -> None:
    """Load an image file

    :param filepath: File Path, Filepath used for importing the file
    :param filter_glob: filter_glob
    """

def load_image(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.jpg;*.png;*.jpeg;*.JPEG;",
) -> None:
    """Load an image file

    :param filepath: File Path, Filepath used for importing the file
    :param filter_glob: filter_glob
    """

def load_sound(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    filepath: str = "",
    filter_glob: str = "*.wav;*.mp3;*.ogg*",
) -> None:
    """Load a sound file

    :param filepath: File Path, Filepath used for importing the file
    :param filter_glob: filter_glob
    """

def move_game_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
    direction: str = "",
) -> None:
    """Move Game Property

    :param index: index
    :param direction: direction
    """

def node_search(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    node: str | None = "",
) -> None:
    """Search for registered Logic Nodes

    :param node: node
    """

def open_donate(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Please consider supporting this Add-On"""

def open_github(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Get involved with development"""

def open_upbge_docs(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """UPBGE API Documentation"""

def open_upbge_manual(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Manual on engine and node usage"""

def pack_new_tree(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    new_tree_name: str = "NewTree",
) -> None:
    """Convert selected Nodes to a new tree. Will be applied to selected object.
    WARNING: All Nodes connected to selection must be selected too

        :param new_tree_name: New Tree Name
    """

def register_custom_node(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    text_name: str | None = "",
) -> None:
    """Register Custom Logic Node

    :param text_name: Node, Register a node defined in a python file
    """

def reload_components(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Reload all components applied to this object"""

def reload_texts(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Reload all externally saved scripts"""

def remove_custom_node(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Remove Custom Logic Node

    :param index: index
    """

def remove_game_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Remove this property

    :param index: index
    """

def remove_global_category(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Remove a global value category"""

def remove_global_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Remove a value accessible from anywhere"""

def remove_logic_tree_property(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    prop_index: int | None = 0,
) -> None:
    """Remove a value accessible from anywhere

    :param prop_index: prop_index
    """

def remove_socket(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Remove this socket"""

def reset_empty_scale(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Reset the volume scale"""

def save_custom_node(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    index: int | None = 0,
) -> None:
    """Save Custom Logic Node

    :param index: index
    """

def start_ui_preview(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
) -> None:
    """Show this canvas and its children. Children are determined by connected Widget sockets, Condition sockets dont matter"""

def unapply_logic_tree(
    execution_context: int | str | None = None,
    undo: bool | None = None,
    /,
    *,
    tree_name: str = "",
    from_obj_name: str = "",
) -> None:
    """Remove the tree from the selected objects

    :param tree_name: tree_name
    :param from_obj_name: from_obj_name
    """
