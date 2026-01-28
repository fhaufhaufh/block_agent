; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude Arm_IO_State.msg.html

(cl:defclass <Arm_IO_State> (roslisp-msg-protocol:ros-message)
  ((Arm_Digital_Input
    :reader Arm_Digital_Input
    :initarg :Arm_Digital_Input
    :type (cl:vector cl:fixnum)
   :initform (cl:make-array 4 :element-type 'cl:fixnum :initial-element 0)))
)

(cl:defclass Arm_IO_State (<Arm_IO_State>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Arm_IO_State>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Arm_IO_State)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<Arm_IO_State> is deprecated: use rm_msgs-msg:Arm_IO_State instead.")))

(cl:ensure-generic-function 'Arm_Digital_Input-val :lambda-list '(m))
(cl:defmethod Arm_Digital_Input-val ((m <Arm_IO_State>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:Arm_Digital_Input-val is deprecated.  Use rm_msgs-msg:Arm_Digital_Input instead.")
  (Arm_Digital_Input m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Arm_IO_State>) ostream)
  "Serializes a message object of type '<Arm_IO_State>"
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let* ((signed ele) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 256) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    ))
   (cl:slot-value msg 'Arm_Digital_Input))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Arm_IO_State>) istream)
  "Deserializes a message object of type '<Arm_IO_State>"
  (cl:setf (cl:slot-value msg 'Arm_Digital_Input) (cl:make-array 4))
  (cl:let ((vals (cl:slot-value msg 'Arm_Digital_Input)))
    (cl:dotimes (i 4)
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:aref vals i) (cl:if (cl:< unsigned 128) unsigned (cl:- unsigned 256))))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Arm_IO_State>)))
  "Returns string type for a message object of type '<Arm_IO_State>"
  "rm_msgs/Arm_IO_State")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Arm_IO_State)))
  "Returns string type for a message object of type 'Arm_IO_State"
  "rm_msgs/Arm_IO_State")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Arm_IO_State>)))
  "Returns md5sum for a message object of type '<Arm_IO_State>"
  "5efdb4b2ffe84170bedb7e7c57e4e694")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Arm_IO_State)))
  "Returns md5sum for a message object of type 'Arm_IO_State"
  "5efdb4b2ffe84170bedb7e7c57e4e694")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Arm_IO_State>)))
  "Returns full string definition for message of type '<Arm_IO_State>"
  (cl:format cl:nil "int8[4] Arm_Digital_Input~%#float32[4] Arm_Analog_Input~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Arm_IO_State)))
  "Returns full string definition for message of type 'Arm_IO_State"
  (cl:format cl:nil "int8[4] Arm_Digital_Input~%#float32[4] Arm_Analog_Input~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Arm_IO_State>))
  (cl:+ 0
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'Arm_Digital_Input) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 1)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Arm_IO_State>))
  "Converts a ROS message object to a list"
  (cl:list 'Arm_IO_State
    (cl:cons ':Arm_Digital_Input (Arm_Digital_Input msg))
))
