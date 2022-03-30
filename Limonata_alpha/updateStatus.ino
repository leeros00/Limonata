// update status in progress

void updateStatus(void){
	ledStatus = 1;
	if ((pumpQ > 0) or (valveQ > 0) or (agitatorQ > 0)){
		ledStatus = 2;
	}
	if (alarmStatus > 0){
		ledStatus += 2;
	}
	
	if (millis() < ledTimeout){
		analogWrite(pinLED, LED);
	}
	else{
		switch (ledStatus){
			case 1: // normal operation, all objects off
				analogWrite(pinLED, loLED);
				break;
			case 2: // normal operation, all the 
        analogWrite(pinLED, hiLED);
