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

class Force_Position_State {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.joint = null;
      this.force = null;
      this.arm_err = null;
      this.dof = null;
    }
    else {
      if (initObj.hasOwnProperty('joint')) {
        this.joint = initObj.joint
      }
      else {
        this.joint = [];
      }
      if (initObj.hasOwnProperty('force')) {
        this.force = initObj.force
      }
      else {
        this.force = 0.0;
      }
      if (initObj.hasOwnProperty('arm_err')) {
        this.arm_err = initObj.arm_err
      }
      else {
        this.arm_err = 0;
      }
      if (initObj.hasOwnProperty('dof')) {
        this.dof = initObj.dof
      }
      else {
        this.dof = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Force_Position_State
    // Serialize message field [joint]
    bufferOffset = _arraySerializer.float32(obj.joint, buffer, bufferOffset, null);
    // Serialize message field [force]
    bufferOffset = _serializer.float32(obj.force, buffer, bufferOffset);
    // Serialize message field [arm_err]
    bufferOffset = _serializer.uint16(obj.arm_err, buffer, bufferOffset);
    // Serialize message field [dof]
    bufferOffset = _serializer.uint8(obj.dof, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Force_Position_State
    let len;
    let data = new Force_Position_State(null);
    // Deserialize message field [joint]
    data.joint = _arrayDeserializer.float32(buffer, bufferOffset, null)
    // Deserialize message field [force]
    data.force = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [arm_err]
    data.arm_err = _deserializer.uint16(buffer, bufferOffset);
    // Deserialize message field [dof]
    data.dof = _deserializer.uint8(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += 4 * object.joint.length;
    return length + 11;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/Force_Position_State';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '73ff0e69e07c4dc10e08479dd9d3ff92';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    float32[] joint
    float32 force
    uint16 arm_err
    uint8 dof
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Force_Position_State(null);
    if (msg.joint !== undefined) {
      resolved.joint = msg.joint;
    }
    else {
      resolved.joint = []
    }

    if (msg.force !== undefined) {
      resolved.force = msg.force;
    }
    else {
      resolved.force = 0.0
    }

    if (msg.arm_err !== undefined) {
      resolved.arm_err = msg.arm_err;
    }
    else {
      resolved.arm_err = 0
    }

    if (msg.dof !== undefined) {
      resolved.dof = msg.dof;
    }
    else {
      resolved.dof = 0
    }

    return resolved;
    }
};

module.exports = Force_Position_State;
