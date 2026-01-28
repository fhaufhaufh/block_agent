
"use strict";

let GetArmState_Command = require('./GetArmState_Command.js');
let MoveJ = require('./MoveJ.js');
let MoveC = require('./MoveC.js');
let Joint_Max_Speed = require('./Joint_Max_Speed.js');
let Arm_Analog_Output = require('./Arm_Analog_Output.js');
let Cabinet = require('./Cabinet.js');
let Stop_Teach = require('./Stop_Teach.js');
let Joint_Current = require('./Joint_Current.js');
let Joint_Step = require('./Joint_Step.js');
let IO_Update = require('./IO_Update.js');
let ChangeTool_State = require('./ChangeTool_State.js');
let Set_Force_Position = require('./Set_Force_Position.js');
let Start_Multi_Drag_Teach = require('./Start_Multi_Drag_Teach.js');
let MoveL = require('./MoveL.js');
let Joint_Error_Code = require('./Joint_Error_Code.js');
let Lift_Height = require('./Lift_Height.js');
let write_single_register = require('./write_single_register.js');
let Six_Force = require('./Six_Force.js');
let MoveJ_P = require('./MoveJ_P.js');
let Servo_GetAngle = require('./Servo_GetAngle.js');
let Force_Position_Move_Joint = require('./Force_Position_Move_Joint.js');
let set_modbus_mode = require('./set_modbus_mode.js');
let Arm_Joint_Speed_Max = require('./Arm_Joint_Speed_Max.js');
let Arm_Digital_Output = require('./Arm_Digital_Output.js');
let Tool_Analog_Output = require('./Tool_Analog_Output.js');
let Servo_Move = require('./Servo_Move.js');
let Gripper_Pick = require('./Gripper_Pick.js');
let Pos_Teach = require('./Pos_Teach.js');
let Tool_IO_State = require('./Tool_IO_State.js');
let ChangeTool_Name = require('./ChangeTool_Name.js');
let ArmState = require('./ArmState.js');
let Arm_IO_State = require('./Arm_IO_State.js');
let Force_Position_Move_Pose = require('./Force_Position_Move_Pose.js');
let Plan_State = require('./Plan_State.js');
let Stop = require('./Stop.js');
let ChangeWorkFrame_State = require('./ChangeWorkFrame_State.js');
let Hand_Posture = require('./Hand_Posture.js');
let Force_Position_State = require('./Force_Position_State.js');
let Ort_Teach = require('./Ort_Teach.js');
let Arm_Current_State = require('./Arm_Current_State.js');
let CartePos = require('./CartePos.js');
let Hand_Seq = require('./Hand_Seq.js');
let Hand_Speed = require('./Hand_Speed.js');
let Lift_Speed = require('./Lift_Speed.js');
let Tool_Digital_Output = require('./Tool_Digital_Output.js');
let Turtle_Driver = require('./Turtle_Driver.js');
let Hand_Force = require('./Hand_Force.js');
let Hand_Angle = require('./Hand_Angle.js');
let Joint_Enable = require('./Joint_Enable.js');
let JointPos = require('./JointPos.js');
let write_register = require('./write_register.js');
let ChangeWorkFrame_Name = require('./ChangeWorkFrame_Name.js');
let Set_Realtime_Push = require('./Set_Realtime_Push.js');
let Gripper_Set = require('./Gripper_Set.js');
let LiftState = require('./LiftState.js');
let Joint_Teach = require('./Joint_Teach.js');
let Manual_Set_Force_Pose = require('./Manual_Set_Force_Pose.js');
let Socket_Command = require('./Socket_Command.js');

module.exports = {
  GetArmState_Command: GetArmState_Command,
  MoveJ: MoveJ,
  MoveC: MoveC,
  Joint_Max_Speed: Joint_Max_Speed,
  Arm_Analog_Output: Arm_Analog_Output,
  Cabinet: Cabinet,
  Stop_Teach: Stop_Teach,
  Joint_Current: Joint_Current,
  Joint_Step: Joint_Step,
  IO_Update: IO_Update,
  ChangeTool_State: ChangeTool_State,
  Set_Force_Position: Set_Force_Position,
  Start_Multi_Drag_Teach: Start_Multi_Drag_Teach,
  MoveL: MoveL,
  Joint_Error_Code: Joint_Error_Code,
  Lift_Height: Lift_Height,
  write_single_register: write_single_register,
  Six_Force: Six_Force,
  MoveJ_P: MoveJ_P,
  Servo_GetAngle: Servo_GetAngle,
  Force_Position_Move_Joint: Force_Position_Move_Joint,
  set_modbus_mode: set_modbus_mode,
  Arm_Joint_Speed_Max: Arm_Joint_Speed_Max,
  Arm_Digital_Output: Arm_Digital_Output,
  Tool_Analog_Output: Tool_Analog_Output,
  Servo_Move: Servo_Move,
  Gripper_Pick: Gripper_Pick,
  Pos_Teach: Pos_Teach,
  Tool_IO_State: Tool_IO_State,
  ChangeTool_Name: ChangeTool_Name,
  ArmState: ArmState,
  Arm_IO_State: Arm_IO_State,
  Force_Position_Move_Pose: Force_Position_Move_Pose,
  Plan_State: Plan_State,
  Stop: Stop,
  ChangeWorkFrame_State: ChangeWorkFrame_State,
  Hand_Posture: Hand_Posture,
  Force_Position_State: Force_Position_State,
  Ort_Teach: Ort_Teach,
  Arm_Current_State: Arm_Current_State,
  CartePos: CartePos,
  Hand_Seq: Hand_Seq,
  Hand_Speed: Hand_Speed,
  Lift_Speed: Lift_Speed,
  Tool_Digital_Output: Tool_Digital_Output,
  Turtle_Driver: Turtle_Driver,
  Hand_Force: Hand_Force,
  Hand_Angle: Hand_Angle,
  Joint_Enable: Joint_Enable,
  JointPos: JointPos,
  write_register: write_register,
  ChangeWorkFrame_Name: ChangeWorkFrame_Name,
  Set_Realtime_Push: Set_Realtime_Push,
  Gripper_Set: Gripper_Set,
  LiftState: LiftState,
  Joint_Teach: Joint_Teach,
  Manual_Set_Force_Pose: Manual_Set_Force_Pose,
  Socket_Command: Socket_Command,
};
