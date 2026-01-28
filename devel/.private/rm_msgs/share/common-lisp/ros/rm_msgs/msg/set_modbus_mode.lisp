; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude set_modbus_mode.msg.html

(cl:defclass <set_modbus_mode> (roslisp-msg-protocol:ros-message)
  ((port
    :reader port
    :initarg :port
    :type cl:fixnum
    :initform 0)
   (baudrate
    :reader baudrate
    :initarg :baudrate
    :type cl:integer
    :initform 0)
   (timeout
    :reader timeout
    :initarg :timeout
    :type cl:fixnum
    :initform 0))
)

(cl:defclass set_modbus_mode (<set_modbus_mode>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <set_modbus_mode>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'set_modbus_mode)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<set_modbus_mode> is deprecated: use rm_msgs-msg:set_modbus_mode instead.")))

(cl:ensure-generic-function 'port-val :lambda-list '(m))
(cl:defmethod port-val ((m <set_modbus_mode>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:port-val is deprecated.  Use rm_msgs-msg:port instead.")
  (port m))

(cl:ensure-generic-function 'baudrate-val :lambda-list '(m))
(cl:defmethod baudrate-val ((m <set_modbus_mode>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:baudrate-val is deprecated.  Use rm_msgs-msg:baudrate instead.")
  (baudrate m))

(cl:ensure-generic-function 'timeout-val :lambda-list '(m))
(cl:defmethod timeout-val ((m <set_modbus_mode>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:timeout-val is deprecated.  Use rm_msgs-msg:timeout instead.")
  (timeout m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <set_modbus_mode>) ostream)
  "Serializes a message object of type '<set_modbus_mode>"
  (cl:let* ((signed (cl:slot-value msg 'port)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 256) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'baudrate)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let* ((signed (cl:slot-value msg 'timeout)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 65536) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <set_modbus_mode>) istream)
  "Deserializes a message object of type '<set_modbus_mode>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'port) (cl:if (cl:< unsigned 128) unsigned (cl:- unsigned 256))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'baudrate) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'timeout) (cl:if (cl:< unsigned 32768) unsigned (cl:- unsigned 65536))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<set_modbus_mode>)))
  "Returns string type for a message object of type '<set_modbus_mode>"
  "rm_msgs/set_modbus_mode")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'set_modbus_mode)))
  "Returns string type for a message object of type 'set_modbus_mode"
  "rm_msgs/set_modbus_mode")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<set_modbus_mode>)))
  "Returns md5sum for a message object of type '<set_modbus_mode>"
  "6163070760cb79680dfbd36751deebbe")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'set_modbus_mode)))
  "Returns md5sum for a message object of type 'set_modbus_mode"
  "6163070760cb79680dfbd36751deebbe")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<set_modbus_mode>)))
  "Returns full string definition for message of type '<set_modbus_mode>"
  (cl:format cl:nil "int8 port~%int32 baudrate~%int16 timeout~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'set_modbus_mode)))
  "Returns full string definition for message of type 'set_modbus_mode"
  (cl:format cl:nil "int8 port~%int32 baudrate~%int16 timeout~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <set_modbus_mode>))
  (cl:+ 0
     1
     4
     2
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <set_modbus_mode>))
  "Converts a ROS message object to a list"
  (cl:list 'set_modbus_mode
    (cl:cons ':port (port msg))
    (cl:cons ':baudrate (baudrate msg))
    (cl:cons ':timeout (timeout msg))
))
