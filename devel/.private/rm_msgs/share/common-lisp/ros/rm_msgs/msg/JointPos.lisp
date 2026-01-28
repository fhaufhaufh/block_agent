; Auto-generated. Do not edit!


(cl:in-package rm_msgs-msg)


;//! \htmlinclude JointPos.msg.html

(cl:defclass <JointPos> (roslisp-msg-protocol:ros-message)
  ((joint
    :reader joint
    :initarg :joint
    :type (cl:vector cl:float)
   :initform (cl:make-array 0 :element-type 'cl:float :initial-element 0.0))
   (expand
    :reader expand
    :initarg :expand
    :type cl:float
    :initform 0.0))
)

(cl:defclass JointPos (<JointPos>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <JointPos>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'JointPos)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name rm_msgs-msg:<JointPos> is deprecated: use rm_msgs-msg:JointPos instead.")))

(cl:ensure-generic-function 'joint-val :lambda-list '(m))
(cl:defmethod joint-val ((m <JointPos>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:joint-val is deprecated.  Use rm_msgs-msg:joint instead.")
  (joint m))

(cl:ensure-generic-function 'expand-val :lambda-list '(m))
(cl:defmethod expand-val ((m <JointPos>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader rm_msgs-msg:expand-val is deprecated.  Use rm_msgs-msg:expand instead.")
  (expand m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <JointPos>) ostream)
  "Serializes a message object of type '<JointPos>"
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'joint))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:let ((bits (roslisp-utils:encode-single-float-bits ele)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream)))
   (cl:slot-value msg 'joint))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'expand))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <JointPos>) istream)
  "Deserializes a message object of type '<JointPos>"
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'joint) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'joint)))
    (cl:dotimes (i __ros_arr_len)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:aref vals i) (roslisp-utils:decode-single-float-bits bits))))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'expand) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<JointPos>)))
  "Returns string type for a message object of type '<JointPos>"
  "rm_msgs/JointPos")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'JointPos)))
  "Returns string type for a message object of type 'JointPos"
  "rm_msgs/JointPos")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<JointPos>)))
  "Returns md5sum for a message object of type '<JointPos>"
  "278dfe354f7a05e095637c9789d0fcfe")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'JointPos)))
  "Returns md5sum for a message object of type 'JointPos"
  "278dfe354f7a05e095637c9789d0fcfe")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<JointPos>)))
  "Returns full string definition for message of type '<JointPos>"
  (cl:format cl:nil "#control arm joints without planning~%~%float32[] joint~%float32    expand~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'JointPos)))
  "Returns full string definition for message of type 'JointPos"
  (cl:format cl:nil "#control arm joints without planning~%~%float32[] joint~%float32    expand~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <JointPos>))
  (cl:+ 0
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'joint) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 4)))
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <JointPos>))
  "Converts a ROS message object to a list"
  (cl:list 'JointPos
    (cl:cons ':joint (joint msg))
    (cl:cons ':expand (expand msg))
))
