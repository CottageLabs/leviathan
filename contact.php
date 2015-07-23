<?php

require_once '/var/www/mandrill-php-api/src/Mandrill.php';
$mandrill = new Mandrill('P60UtzC-pFXJzjHnadNQtQ');

# ========================================================

$replyemail="michelle.lynver@gmail.com";
$replyname='Michelle Williams';
$redirect = 'http://lynver.co.uk/thanks';
$valid_ref1="lynver.co.uk";
$valid_ref2="www.lynver.co.uk";
$check = true;
$checkemail = "mark@cottagelabs.com";
$checkname = "Mark MacGillivray";

# ========================================================

$ref_page=$_SERVER["HTTP_HOST"];
$valid_referrer=0;
if($ref_page===$valid_ref1) $valid_referrer=1;
elseif($ref_page===$valid_ref2) $valid_referrer=1;
if((!$valid_referrer) OR ($_POST["touring"]!=12)) {
    echo $ref_page . " ";
    echo $_POST . " ";
    echo "query invalid. aborting.";
    exit;
}

function is_forbidden($str,$check_all_patterns = true) {
    $patterns[0] = '/content-type:/';
    $patterns[1] = '/mime-version/';
    $patterns[2] = '/multipart/';
    $patterns[3] = '/Content-Transfer-Encoding/';
    $patterns[4] = '/to:/';
    $patterns[5] = '/cc:/';
    $patterns[6] = '/bcc:/';
    $forbidden = 0;
    for ($i=0; $i<count($patterns); $i++) {
        $forbidden = preg_match($patterns[$i], strtolower($str));
        if ($forbidden) break;
    }
    if ($check_all_patterns AND !$forbidden) $forbidden = preg_match("/(%0a|%0d|\\n+|\\r+)/i", $str);
    if ($forbidden) {
        echo "<font color=red><center><h3>STOP! Message not sent.</font></h3><br><b>
            The text you entered is forbidden, it includes one or more of the following:
            <br><textarea rows=9 cols=25>";
        foreach ($patterns as $key => $value) echo trim($value,"/")."\n";
        echo "</textarea><br>Click back on your browser, remove the above characters and try again.";
        exit();
    }
}

foreach ($_REQUEST as $key => $value) {
    if ($key == "message") is_forbidden($value, false);
    else is_forbidden($value);
}

$name = $_POST["name"];
$phone = $_POST["phone"];
$email = $_POST["email"];
$nights = $_POST["nights"];
$guests = $_POST["guests"];
$commencing = $_POST["commencing"];
$themessage = $_POST["message"];

$replymessage = "Hi $name

Thank you for your email.

We will endeavour to reply to you shortly.

Please DO NOT reply to this email - it is an automated system response.

Below is a copy of the message you submitted:
--------------------------------------------------
Query:
$themessage
--------------------------------------------------

Thank you";

$message = "name: $name \nphone: $phone \nemail: $email \nnights: $nights \nguests: $guests \ncommencing: $commencing \n\nquery: \n$themessage";

#mail("$replyemail",
#     "message from $valid_ref1",
#     "$message",
#     "From: $email\nReply-To: $email");

$alert = array(
    'text' => $message,
    'subject' => "message from $valid_ref1",
    'from_email' => $email,
    'headers' => array('Reply-To' => $email),
    'to' => array(
        array(
            'email' => $replyemail,
            'name' => $replyname,
            'type' => 'to'
        )
    )
);
$mandrill->messages->send($alert);

$confirm = array(
    'text' => $replymessage,
    'subject' => "Receipt: Your query to $valid_ref1",
    'from_email' => $replyemail,
    'headers' => array('Reply-To' => $replyemail),
    'to' => array(
        array(
            'email' => $email,
            'name' => $name,
            'type' => 'to'
        )
    )
);
$mandrill->messages->send($confirm);

if ( $check ) {
    $checker = array(
        'text' => $message,
        'subject' => "observing message from $valid_ref1",
        'from_email' => $email,
        'headers' => array('Reply-To' => $email),
        'to' => array(
            array(
                'email' => $checkemail,
                'name' => $checkname,
                'type' => 'to'
            )
        )
    );
    $mandrill->messages->send($checker);
}

header("Location: $redirect");
#echo " query submitted. thanks.";

?>
