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

class Tool_IO_State {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.Tool_IO_Mode = null;
      this.Tool_IO_State = null;
    }
    else {
      if (initObj.hasOwnProperty('Tool_IO_Mode')) {
        this.Tool_IO_Mode = initObj.Tool_IO_Mode
      }
      else {
        this.Tool_IO_Mode = new Array(2).fill(0);
      }
      if (initObj.hasOwnProperty('Tool_IO_State')) {
        this.Tool_IO_State = initObj.Tool_IO_State
      }
      else {
        this.Tool_IO_State = new Array(2).fill(0);
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Tool_IO_State
    // Check that the constant length array field [Tool_IO_Mode] has the right length
    if (obj.Tool_IO_Mode.length !== 2) {
      throw new Error('Unable to serialize array field Tool_IO_Mode - length must be 2')
    }
    // Serialize message field [Tool_IO_Mode]
    bufferOffset = _arraySerializer.bool(obj.Tool_IO_Mode, buffer, bufferOffset, 2);
    // Check that the constant length array field [Tool_IO_State] has the right length
    if (obj.Tool_IO_State.length !== 2) {
      throw new Error('Unable to serialize array field Tool_IO_State - length must be 2')
    }
    // Serialize message field [Tool_IO_State]
    bufferOffset = _arraySerializer.bool(obj.Tool_IO_State, buffer, bufferOffset, 2);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Tool_IO_State
    let len;
    let data = new Tool_IO_State(null);
    // Deserialize message field [Tool_IO_Mode]
    data.Tool_IO_Mode = _arrayDeserializer.bool(buffer, bufferOffset, 2)
    // Deserialize message field [Tool_IO_State]
    data.Tool_IO_State = _arrayDeserializer.bool(buffer, bufferOffset, 2)
    return data;
  }

  static getMessageSize(object) {
    return 4;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/Tool_IO_State';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '8dedcedb3bfd854b3826d29065f33f9d';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool[2] Tool_IO_Mode          #数字I/O输入/输出状态  0-输入模式，1-输出模式
    bool[2] Tool_IO_State         #数字I/O电平状态      0-低，1-高
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Tool_IO_State(null);
    if (msg.Tool_IO_Mode !== undefined) {
      resolved.Tool_IO_Mode = msg.Tool_IO_Mode;
    }
    else {
      resolved.Tool_IO_Mode = new Array(2).fill(0)
    }

    if (msg.Tool_IO_State !== undefined) {
      resolved.Tool_IO_State = msg.Tool_IO_State;
    }
    else {
      resolved.Tool_IO_State = new Array(2).fill(0)
    }

    return resolved;
    }
};

module.exports = Tool_IO_State;
