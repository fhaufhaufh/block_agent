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

class Manual_Set_Force_Pose {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.pose = null;
      this.joint = null;
    }
    else {
      if (initObj.hasOwnProperty('pose')) {
        this.pose = initObj.pose
      }
      else {
        this.pose = '';
      }
      if (initObj.hasOwnProperty('joint')) {
        this.joint = initObj.joint
      }
      else {
        this.joint = [];
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type Manual_Set_Force_Pose
    // Serialize message field [pose]
    bufferOffset = _serializer.string(obj.pose, buffer, bufferOffset);
    // Serialize message field [joint]
    bufferOffset = _arraySerializer.int64(obj.joint, buffer, bufferOffset, null);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type Manual_Set_Force_Pose
    let len;
    let data = new Manual_Set_Force_Pose(null);
    // Deserialize message field [pose]
    data.pose = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [joint]
    data.joint = _arrayDeserializer.int64(buffer, bufferOffset, null)
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.pose);
    length += 8 * object.joint.length;
    return length + 8;
  }

  static datatype() {
    // Returns string type for a message object
    return 'rm_msgs/Manual_Set_Force_Pose';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'aeeb8895b8a7ffa8296b1f7ab18fb600';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    string pose
    int64[] joint
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new Manual_Set_Force_Pose(null);
    if (msg.pose !== undefined) {
      resolved.pose = msg.pose;
    }
    else {
      resolved.pose = ''
    }

    if (msg.joint !== undefined) {
      resolved.joint = msg.joint;
    }
    else {
      resolved.joint = []
    }

    return resolved;
    }
};

module.exports = Manual_Set_Force_Pose;
