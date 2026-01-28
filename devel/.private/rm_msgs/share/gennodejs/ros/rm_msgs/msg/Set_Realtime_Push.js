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

class Set_Realtime_Push {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.cycle = null;
      this.port = null;
      this.force_coordinate = null;
      this.ip = null;
    }
    else {
      if (initObj.hasOwnProperty('cycle')) {
        this.cycle = initObj.cycle
      }
      else {
        this.cycle = 0;
      }
      if (initObj.hasOwnProperty('port')) {
        this.port = initObj.port
      }
      else {
        this.port = 0;
      }
      if (initObj.hasOwnProperty('force_coordinate')) {
        this.force_coordinate = initObj.force_coordinate
      }
      else {
        this.force_coordinate = 0;
      }
      if (initObj.hasOwnProperty('ip')) {
        this.ip = initObj.ip
      }
      else {
        this.ip = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Set_Realtime_Push
    // Serialize message field [cycle]
    bufferOffset = _serializer.uint16(obj.cycle, buffer, bufferOffset);
    // Serialize message field [port]
    bufferOffset = _serializer.uint16(obj.port, buffer, bufferOffset);
    // Serialize message field [force_coordinate]
    bufferOffset = _serializer.uint16(obj.force_coordinate, buffer, bufferOffset);
    // Serialize message field [ip]
    bufferOffset = _serializer.string(obj.ip, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Set_Realtime_Push
    let len;
    let data = new Set_Realtime_Push(null);
    // Deserialize message field [cycle]
    data.cycle = _deserializer.uint16(buffer, bufferOffset);
    // Deserialize message field [port]
    data.port = _deserializer.uint16(buffer, bufferOffset);
    // Deserialize message field [force_coordinate]
    data.force_coordinate = _deserializer.uint16(buffer, bufferOffset);
    // Deserialize message field [ip]
    data.ip = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.ip);
    return length + 10;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/Set_Realtime_Push';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '9a0e0df44121dc8d27005a2fbd40ac91';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    uint16 cycle
    uint16 port
    uint16 force_coordinate
    string ip
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Set_Realtime_Push(null);
    if (msg.cycle !== undefined) {
      resolved.cycle = msg.cycle;
    }
    else {
      resolved.cycle = 0
    }

    if (msg.port !== undefined) {
      resolved.port = msg.port;
    }
    else {
      resolved.port = 0
    }

    if (msg.force_coordinate !== undefined) {
      resolved.force_coordinate = msg.force_coordinate;
    }
    else {
      resolved.force_coordinate = 0
    }

    if (msg.ip !== undefined) {
      resolved.ip = msg.ip;
    }
    else {
      resolved.ip = ''
    }

    return resolved;
    }
};

module.exports = Set_Realtime_Push;
