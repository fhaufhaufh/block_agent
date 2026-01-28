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

class set_modbus_mode {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.port = null;
      this.baudrate = null;
      this.timeout = null;
    }
    else {
      if (initObj.hasOwnProperty('port')) {
        this.port = initObj.port
      }
      else {
        this.port = 0;
      }
      if (initObj.hasOwnProperty('baudrate')) {
        this.baudrate = initObj.baudrate
      }
      else {
        this.baudrate = 0;
      }
      if (initObj.hasOwnProperty('timeout')) {
        this.timeout = initObj.timeout
      }
      else {
        this.timeout = 0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type set_modbus_mode
    // Serialize message field [port]
    bufferOffset = _serializer.int8(obj.port, buffer, bufferOffset);
    // Serialize message field [baudrate]
    bufferOffset = _serializer.int32(obj.baudrate, buffer, bufferOffset);
    // Serialize message field [timeout]
    bufferOffset = _serializer.int16(obj.timeout, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type set_modbus_mode
    let len;
    let data = new set_modbus_mode(null);
    // Deserialize message field [port]
    data.port = _deserializer.int8(buffer, bufferOffset);
    // Deserialize message field [baudrate]
    data.baudrate = _deserializer.int32(buffer, bufferOffset);
    // Deserialize message field [timeout]
    data.timeout = _deserializer.int16(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 7;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/set_modbus_mode';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '6163070760cb79680dfbd36751deebbe';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    int8 port
    int32 baudrate
    int16 timeout
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new set_modbus_mode(null);
    if (msg.port !== undefined) {
      resolved.port = msg.port;
    }
    else {
      resolved.port = 0
    }

    if (msg.baudrate !== undefined) {
      resolved.baudrate = msg.baudrate;
    }
    else {
      resolved.baudrate = 0
    }

    if (msg.timeout !== undefined) {
      resolved.timeout = msg.timeout;
    }
    else {
      resolved.timeout = 0
    }

    return resolved;
    }
};

module.exports = set_modbus_mode;
