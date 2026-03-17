// Auto-generated. Do not edit!

// (in-package rm_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------

class Arm_IO_State {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.Arm_Digital_Input = null;
    }
    else {
      if (initObj.hasOwnProperty('Arm_Digital_Input')) {
        this.Arm_Digital_Input = initObj.Arm_Digital_Input
      }
      else {
        this.Arm_Digital_Input = new Array(4).fill(0);
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Arm_IO_State
    // Check that the constant length array field [Arm_Digital_Input] has the right length
    if (obj.Arm_Digital_Input.length !== 4) {
      throw new Error('Unable to serialize array field Arm_Digital_Input - length must be 4')
    }
    // Serialize message field [Arm_Digital_Input]
    bufferOffset = _arraySerializer.int8(obj.Arm_Digital_Input, buffer, bufferOffset, 4);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Arm_IO_State
    let len;
    let data = new Arm_IO_State(null);
    // Deserialize message field [Arm_Digital_Input]
    data.Arm_Digital_Input = _arrayDeserializer.int8(buffer, bufferOffset, 4)
    return data;
  }

  static getMessageSize(object) {
    return 4;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/Arm_IO_State';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '5efdb4b2ffe84170bedb7e7c57e4e694';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int8[4] Arm_Digital_Input
    #float32[4] Arm_Analog_Input
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Arm_IO_State(null);
    if (msg.Arm_Digital_Input !== undefined) {
      resolved.Arm_Digital_Input = msg.Arm_Digital_Input;
    }
    else {
      resolved.Arm_Digital_Input = new Array(4).fill(0)
    }

    return resolved;
    }
};

module.exports = Arm_IO_State;
