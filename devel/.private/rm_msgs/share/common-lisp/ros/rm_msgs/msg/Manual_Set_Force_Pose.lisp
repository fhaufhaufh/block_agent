; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude Manual_Set_Force_Pose.msg.html

(cl:defclass <Manual_Set_Force_Pose> (roslisp-msg-protocol:ros-message)
  ((pose
    :reader pose
    :initarg :pose
    :type cl:string
    :initform "")
   (joint
    :reader joint
    :initarg :joint
    :type (cl:vector cl:integer)
   :initform (cl:make-array 0 :element-type 'cl:integer :initial-element 0)))
)

(cl:defclass Manual_Set_Force_Pose (<Manual_Set_Force_Pose>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <Manual_Set_Force_Pose>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'Manual_Set_Force_Pose)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<Manual_Set_Force_Pose> is deprecated: use rm_msgs-msg:Manual_Set_Force_Pose instead.")))

(cl:ensure-generic-function 'pose-val :lambda-list '(m))
(cl:defmethod pose-val ((m <Manual_Set_Force_Pose>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:pose-val is deprecated.  Use rm_msgs-msg:pose instead.")
  (pose m))

(cl:ensure-generic-function 'joint-val :lambda-list '(m))
(cl:defmethod joint-val ((m <Manual_Set_Force_Pose>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:joint-val is deprecated.  Use rm_msgs-msg:joint instead.")
  (joint m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <Manual_Set_Force_Pose>) ostream)
  "Serializes a message object of type '<Manual_Set_Force_Pose>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'pose))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'pose))
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'joint))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let* ((signed ele) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 18446744073709551616) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) unsigned) ostream)
    ))
   (cl:slot-value msg 'joint))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <Manual_Set_Force_Pose>) istream)
  "Deserializes a message object of type '<Manual_Set_Force_Pose>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'pose) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'pose) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'joint) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'joint)))
    (cl:dotimes (i __ros_arr_len)
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) unsigned) (cl:read-byte istream))
      (cl:setf (cl:aref vals i) (cl:if (cl:< unsigned 9223372036854775808) unsigned (cl:- unsigned 18446744073709551616)))))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<Manual_Set_Force_Pose>)))
  "Returns string type for a message object of type '<Manual_Set_Force_Pose>"
  "rm_msgs/Manual_Set_Force_Pose")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'Manual_Set_Force_Pose)))
  "Returns string type for a message object of type 'Manual_Set_Force_Pose"
  "rm_msgs/Manual_Set_Force_Pose")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<Manual_Set_Force_Pose>)))
  "Returns md5sum for a message object of type '<Manual_Set_Force_Pose>"
  "aeeb8895b8a7ffa8296b1f7ab18fb600")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'Manual_Set_Force_Pose)))
  "Returns md5sum for a message object of type 'Manual_Set_Force_Pose"
  "aeeb8895b8a7ffa8296b1f7ab18fb600")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<Manual_Set_Force_Pose>)))
  "Returns full string definition for message of type '<Manual_Set_Force_Pose>"
  (cl:format cl:nil "string pose~%int64[] joint~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'Manual_Set_Force_Pose)))
  "Returns full string definition for message of type 'Manual_Set_Force_Pose"
  (cl:format cl:nil "string pose~%int64[] joint~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <Manual_Set_Force_Pose>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'pose))
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'joint) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 8)))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <Manual_Set_Force_Pose>))
  "Converts a ROS message object to a list"
  (cl:list 'Manual_Set_Force_Pose
    (cl:cons ':pose (pose msg))
    (cl:cons ':joint (joint msg))
))
