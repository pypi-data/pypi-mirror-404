"""
Bullet Physics provides collision detection
and rigid body dynamics for the Blender Game Engine.

Features:

* Vehicle simulation.
* Rigid body constraints: hinge and point to point (ball socket).
* Access to internal physics settings,
like deactivation time, and debugging features

[NOTE]
Note about parameter settings
Since this API is not well documented, it can be unclear what kind of values to use for setting parameters.
In general, damping settings should be in the range of 0 to 1 and
stiffness settings should not be much higher than about 10.


--------------------

For more examples of Bullet physics and how to use them
see the pybullet forum.



```../examples/bge.constraints.py```


--------------------


--------------------


--------------------

Debug mode to be used with setDebugMode.


--------------------

Constraint type to be used with createConstraint.

"""

import typing
import collections.abc
import typing_extensions
import numpy.typing as npt

def createConstraint(
    physicsid_1: int,
    physicsid_2: int,
    constraint_type: int,
    pivot_x: float = 0.0,
    pivot_y: float = 0.0,
    pivot_z: float = 0.0,
    axis_x: float = 0.0,
    axis_y: float = 0.0,
    axis_z: float = 0.0,
    flag: int = 0,
) -> None:
    """Creates a constraint.

    :param physicsid_1: The physics id of the first object in constraint.
    :param physicsid_2: The physics id of the second object in constraint.
    :param constraint_type: The type of the constraint, see Create Constraint Constants.
    :param pivot_x: Pivot X position. (optional)
    :param pivot_y: Pivot Y position. (optional)
    :param pivot_z: Pivot Z position. (optional)
    :param axis_x: X axis angle in degrees. (optional)
    :param axis_y: Y axis angle in degrees. (optional)
    :param axis_z: Z axis angle in degrees. (optional)
    :param flag: 128 to disable collision between linked bodies. (optional)
    :return: A constraint wrapper.
    """

def createVehicle(physicsid: int) -> None:
    """Creates a vehicle constraint.

    :param physicsid: The physics id of the chassis object in constraint.
    :return: A vehicle constraint wrapper.
    """

def exportBulletFile(filename: str) -> None:
    """Exports a file representing the dynamics world (usually using .bullet extension).See Bullet binary serialization.

    :param filename: File path.
    """

def getAppliedImpulse(constraintId: int) -> float:
    """

    :param constraintId: The id of the constraint.
    :return: The most recent applied impulse.
    """

def getCharacter(gameobj) -> None:
    """

    :param gameobj: The game object with the character physics.
    :return: Character wrapper.
    """

def getVehicleConstraint(constraintId: int) -> None:
    """

    :param constraintId: The id of the vehicle constraint.
    :return: A vehicle constraint object.
    """

def removeConstraint(constraintId: int) -> None:
    """Removes a constraint.

    :param constraintId: The id of the constraint to be removed.
    """

def setCFM(cfm) -> None:
    """Sets the Constraint Force Mixing (CFM) for soft constraints.
    If the Constraint Force Mixing (CFM) is set to zero, the constraint will be hard.
    If CFM is set to a positive value, it will be possible to violate the constraint by pushing on it (for example, for contact constraints by forcing the two contacting objects together).
    In other words the constraint will be soft, and the softness will increase as CFM increases.

        :param cfm: The CFM parameter for soft constraints.
    """

def setContactBreakingTreshold(breakingTreshold: float) -> None:
    """Sets tresholds to do with contact point management.

    :param breakingTreshold: The new contact breaking treshold.
    """

def setDeactivationAngularTreshold(angularTreshold: float) -> None:
    """Sets the angular velocity treshold.

    :param angularTreshold: New deactivation angular treshold.
    """

def setDeactivationLinearTreshold(linearTreshold: float) -> None:
    """Sets the linear velocity treshold.

    :param linearTreshold: New deactivation linear treshold.
    """

def setDeactivationTime(time: float) -> None:
    """Sets the time after which a resting rigidbody gets deactived.

    :param time: The deactivation time.
    """

def setDebugMode(mode: int) -> None:
    """Sets the debug mode.

    :param mode: The new debug mode, see Debug Mode Constants.
    """

def setERPContact(erp2) -> None:
    """Sets the Error Reduction Parameter (ERP) for contact constraints.
    The Error Reduction Parameter (ERP) specifies what proportion of the joint error will be fixed during the next simulation step.
    If ERP = 0.0 then no correcting force is applied and the bodies will eventually drift apart as the simulation proceeds.
    If ERP = 1.0 then the simulation will attempt to fix all joint error during the next time step.
    However, setting ERP = 1.0 is not recommended, as the joint error will not be completely fixed due to various internal approximations.
    A value of ERP = 0.1 to 0.8 is recommended.

        :param erp2: The ERP parameter for contact constraints.
    """

def setERPNonContact(erp) -> None:
    """Sets the Error Reduction Parameter (ERP) for non-contact constraints.
    The Error Reduction Parameter (ERP) specifies what proportion of the joint error will be fixed during the next simulation step.
    If ERP = 0.0 then no correcting force is applied and the bodies will eventually drift apart as the simulation proceeds.
    If ERP = 1.0 then the simulation will attempt to fix all joint error during the next time step.
    However, setting ERP = 1.0 is not recommended, as the joint error will not be completely fixed due to various internal approximations.
    A value of ERP = 0.1 to 0.8 is recommended.

        :param erp: The ERP parameter for non-contact constraints.
    """

def setGravity(x: float, y: float, z: float) -> None:
    """Sets the gravity force.Sets the linear air damping for rigidbodies.

    :param x: Gravity X force.
    :param y: Gravity Y force.
    :param z: Gravity Z force.
    """

def setNumIterations(numiter: int) -> None:
    """Sets the number of iterations for an iterative constraint solver.

    :param numiter: New number of iterations.
    """

def setNumTimeSubSteps(numsubstep: int) -> None:
    """Sets the number of substeps for each physics proceed. Tradeoff quality for performance.

    :param numsubstep: New number of substeps.
    """

def setSolverDamping(damping: float) -> None:
    """Sets the damper constant of a penalty based solver.

    :param damping: New damping for the solver.
    """

def setSolverTau(tau: float) -> None:
    """Sets the spring constant of a penalty based solver.

    :param tau: New tau for the solver.
    """

def setSolverType(solverType: int) -> None:
    """Sets the solver type.

    :param solverType: The new type of the solver.
    """

def setSorConstant(sor: float) -> None:
    """Sets the successive overrelaxation constant.

    :param sor: New sor value.
    """

ANGULAR_CONSTRAINT: int

CONETWIST_CONSTRAINT: int

DBG_DISABLEBULLETLCP: int
""" Disable Bullet LCP.
"""

DBG_DRAWAABB: int
""" Draw Axis Aligned Bounding Box in debug.
"""

DBG_DRAWCONSTRAINTLIMITS: int
""" Draw constraint limits in debug.
"""

DBG_DRAWCONSTRAINTS: int
""" Draw constraints in debug.
"""

DBG_DRAWCONTACTPOINTS: int
""" Draw contact points in debug.
"""

DBG_DRAWFREATURESTEXT: int
""" Draw features text in debug.
"""

DBG_DRAWTEXT: int
""" Draw text in debug.
"""

DBG_DRAWWIREFRAME: int
""" Draw wireframe in debug.
"""

DBG_ENABLECCD: int
""" Enable Continuous Collision Detection in debug.
"""

DBG_ENABLESATCOMPARISION: int
""" Enable sat comparison in debug.
"""

DBG_FASTWIREFRAME: int
""" Draw a fast wireframe in debug.
"""

DBG_NODEBUG: int
""" No debug.
"""

DBG_NOHELPTEXT: int
""" Debug without help text.
"""

DBG_PROFILETIMINGS: int
""" Draw profile timings in debug.
"""

GENERIC_6DOF_CONSTRAINT: int

LINEHINGE_CONSTRAINT: int

POINTTOPOINT_CONSTRAINT: int

VEHICLE_CONSTRAINT: int

error: str
""" Symbolic constant string that indicates error.
"""
