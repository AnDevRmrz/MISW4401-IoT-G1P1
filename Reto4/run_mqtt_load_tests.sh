jmeter_load_test_plan="MQTTLoadTest.jmx"
server="3.223.195.124"
port=8082
username="admin"
password="admin1234"

pub_threads=10
pub_duration=30
pub_thread_duration=$((30*1))
pub_loop=10
pub_loop_count=50

sub_threads=100
sub_duration=30
sub_thread_duration=$((30*1))
sub_loop=30
sub_loop_count=50


LOG_FILE="./test_execution.log"
date=$(date +%Y-%m-%d)
time_stamp=$(date '+%Y_%m_%d_%H_%M_%S')
workdir_path="./results/$time_stamp"

~/programs/apache-jmeter-5.6.3/bin/jmeter -n \
  -t "$jmeter_load_test_plan" \
  -l "$workdir_path/result.jlt" \
  -j "$workdir_path/jmeter.log" \
  -Jserver="$server" \
  -Jport="$port" \
  -Jusername="$username" \
  -Jpassword="$password" \
  -Jpub_threads="$pub_threads" \
  -Jpub_duration="$pub_duration" \
  -Jpub_thread_duration="$pub_thread_duration" \
  -Jpub_loop="$pub_loop" \
  -Jpub_loop_count="$pub_loop_count" \
  -Jsub_threads="$sub_threads" \
  -Jsub_duration="$sub_duration" \
  -Jsub_thread_duration="$sub_thread_duration" \
  -Jsub_loop="$sub_loop" \
  -Jsub_loop_count="$sub_loop_count" \
  -e \
  -o "$workdir_path/report/" 2>&1 | tee -a "$LOG_FILE"