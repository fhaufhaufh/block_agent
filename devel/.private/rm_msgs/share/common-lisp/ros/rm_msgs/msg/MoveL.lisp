; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude MoveL.msg.html

(cl:defclass <MoveL> (roslisp-msg-protocol:ros-message)
  ((Pose
    :reader Pose
    :initarg :Pose
    :type geometry_msgs-msg:Pose
    :initform (cl:make-instance 'geometry_msgs-msg:Pose))
   (speed
    :reader speed
    :initarg :speed
    :type cl:float
    :initform 0.0)
   (trajectory_connect
    :reader trajectory_connect
    :initarg :trajectory_connect
    :type cl:fixnum
    :initform 0))
)

(cl:defclass MoveL (<MoveL>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <MoveL>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'MoveL)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<MoveL> is deprecated: use rm_msgs-msg:MoveL instead.")))

(cl:ensure-generic-function 'Pose-val :lambda-list '(m))
(cl:defmethod Pose-val ((m <MoveL>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:Pose-val is deprecated.  Use rm_msgs-msg:Pose instead.")
  (Pose m))

(cl:ensure-generic-function 'speed-val :lambda-list '(m))
(cl:defmethod speed-val ((m <MoveL>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:speed-val is deprecated.  Use rm_msgs-msg:speed instead.")
  (speed m))

(cl:ensure-generic-function 'trajectory_connect-val :lambda-list '(m))
(cl:defmethod trajectory_connect-val ((m <MoveL>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:trajectory_connect-val is deprecated.  Use rm_msgs-msg:trajectory_connect instead.")
  (trajectory_connect m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <MoveL>) ostream)
  "Serializes a message object of type '<MoveL>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'Pose) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'speed))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trajectory_connect)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <MoveL>) istream)
  "Deserializes a message object of type '<MoveL>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'Pose) istream)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'speed) (roslisp-utils:decode-single-float-bits bits)))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'trajectory_connect)) (cl:read-byte istream))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<MoveL>)))
  "Returns string type for a message object of type '<MoveL>"
  "rm_msgs/MoveL")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'MoveL)))
  "Returns string type for a message object of type 'MoveL"
  "rm_msgs/MoveL")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<MoveL>)))
  "Returns md5sum for a message object of type '<MoveL>"
  "71f8a77c6be4dc679da6e3cd77730408")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'MoveL)))
  "Returns md5sum for a message object of type 'MoveL"
  "71f8a77c6be4dc679da6e3cd77730408")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<MoveL>)))
  "Returns full string definition for message of type '<MoveL>"
  (cl:format cl:nil "geometry_msgs/Pose Pose~%float32 speed~%uint8 trajectory_connect~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'MoveL)))
  "Returns full string definition for message of type 'MoveL"
  (cl:format cl:nil "geometry_msgs/Pose Pose~%float32 speed~%uint8 trajectory_connect~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <MoveL>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'Pose))
     4
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <MoveL>))
  "Converts a ROS message object to a list"
  (cl:list 'MoveL
    (cl:cons ':Pose (Pose msg))
    (cl:cons ':speed (speed msg))
    (cl:cons ':trajectory_connect (trajectory_connect msg))
))
