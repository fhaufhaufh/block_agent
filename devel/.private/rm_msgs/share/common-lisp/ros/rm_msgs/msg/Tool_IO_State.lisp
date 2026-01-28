; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude Tool_IO_State.msg.html

(cl:defclass <Tool_IO_State> (roslisp-msg-protocol:ros-message)
  ((Tool_IO_Mode
    :reader Tool_IO_Mode
    :initarg :Tool_IO_Mode
    :type (cl:vector cl:boolean)
   :initform (cl:make-array 2 :element-type 'cl:boolean :initial-element cl:nil))
   (Tool_IO_State
    :reader Tool_IO_State
    :initarg :Tool_IO_State
    :type (cl:vector cl:boolean)
   :initform (cl:make-array 2 :element-type 'cl:boolean :initial-element cl:nil)))
)

(cl:defclass Tool_IO_State (<Tool_IO_State>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Tool_IO_State>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Tool_IO_State)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<Tool_IO_State> is deprecated: use rm_msgs-msg:Tool_IO_State instead.")))

(cl:ensure-generic-function 'Tool_IO_Mode-val :lambda-list '(m))
(cl:defmethod Tool_IO_Mode-val ((m <Tool_IO_State>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:Tool_IO_Mode-val is deprecated.  Use rm_msgs-msg:Tool_IO_Mode instead.")
  (Tool_IO_Mode m))

(cl:ensure-generic-function 'Tool_IO_State-val :lambda-list '(m))
(cl:defmethod Tool_IO_State-val ((m <Tool_IO_State>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:Tool_IO_State-val is deprecated.  Use rm_msgs-msg:Tool_IO_State instead.")
  (Tool_IO_State m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Tool_IO_State>) ostream)
  "Serializes a message object of type '<Tool_IO_State>"
  (cl:map cl:nil #'(cl:lambda (ele) (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if ele 1 0)) ostream))
   (cl:slot-value msg 'Tool_IO_Mode))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if ele 1 0)) ostream))
   (cl:slot-value msg 'Tool_IO_State))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Tool_IO_State>) istream)
  "Deserializes a message object of type '<Tool_IO_State>"
  (cl:setf (cl:slot-value msg 'Tool_IO_Mode) (cl:make-array 2))
  (cl:let ((vals (cl:slot-value msg 'Tool_IO_Mode)))
    (cl:dotimes (i 2)
    (cl:setf (cl:aref vals i) (cl:not (cl:zerop (cl:read-byte istream))))))
  (cl:setf (cl:slot-value msg 'Tool_IO_State) (cl:make-array 2))
  (cl:let ((vals (cl:slot-value msg 'Tool_IO_State)))
    (cl:dotimes (i 2)
    (cl:setf (cl:aref vals i) (cl:not (cl:zerop (cl:read-byte istream))))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Tool_IO_State>)))
  "Returns string type for a message object of type '<Tool_IO_State>"
  "rm_msgs/Tool_IO_State")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Tool_IO_State)))
  "Returns string type for a message object of type 'Tool_IO_State"
  "rm_msgs/Tool_IO_State")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Tool_IO_State>)))
  "Returns md5sum for a message object of type '<Tool_IO_State>"
  "8dedcedb3bfd854b3826d29065f33f9d")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Tool_IO_State)))
  "Returns md5sum for a message object of type 'Tool_IO_State"
  "8dedcedb3bfd854b3826d29065f33f9d")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Tool_IO_State>)))
  "Returns full string definition for message of type '<Tool_IO_State>"
  (cl:format cl:nil "bool[2] Tool_IO_Mode          #数字I/O输入/输出状态  0-输入模式，1-输出模式~%bool[2] Tool_IO_State         #数字I/O电平状态      0-低，1-高~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Tool_IO_State)))
  "Returns full string definition for message of type 'Tool_IO_State"
  (cl:format cl:nil "bool[2] Tool_IO_Mode          #数字I/O输入/输出状态  0-输入模式，1-输出模式~%bool[2] Tool_IO_State         #数字I/O电平状态      0-低，1-高~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Tool_IO_State>))
  (cl:+ 0
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'Tool_IO_Mode) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 1)))
     0 (cl:reduce #'cl:+ (cl:slot-value msg 'Tool_IO_State) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 1)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Tool_IO_State>))
  "Converts a ROS message object to a list"
  (cl:list 'Tool_IO_State
    (cl:cons ':Tool_IO_Mode (Tool_IO_Mode msg))
    (cl:cons ':Tool_IO_State (Tool_IO_State msg))
))
