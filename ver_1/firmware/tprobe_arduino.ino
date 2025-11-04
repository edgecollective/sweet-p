/***********************************************************
      DFRobot Gravity: Analog Current to Voltage Converter(For 4~20mA Application)
      SKU:SEN0262

      GNU Lesser General Public License.
      See <http://www.gnu.org/licenses/> for details.
      All above must be included in any redistribution
     ****************************************************/

    #define ANALOG_PIN A2
    #define RANGE 5000 // Depth measuring range 5000mm (for water)
    #define VREF 5000 // ADC's reference voltage on your Arduino,typical value:5000mV
    #define CURRENT_INIT 4.00 // Current @ 0mm (uint: mA)
    #define DENSITY_WATER 1  // Pure water density normalized to 1
    #define DENSITY_GASOLINE 0.74  // Gasoline density
    #define PRINT_INTERVAL 1000

    int16_t dataVoltage;
    float dataCurrent, depth; //unit:mA
    unsigned long timepoint_measure;

    void setup()
    {
      Serial.begin(9600);
      pinMode(ANALOG_PIN, INPUT);
      timepoint_measure = millis();
    }

    void loop()
    {
      if (millis() - timepoint_measure > PRINT_INTERVAL) {
        timepoint_measure = millis();

        dataVoltage = analogRead(ANALOG_PIN)/ 1024.0 * VREF;
        dataCurrent = dataVoltage / 120.0; //Sense Resistor:120ohm
        depth = (dataCurrent - CURRENT_INIT) * (RANGE/ DENSITY_WATER / 16.0); //Calculate depth from current readings

        if (depth < 0) 
        {
          depth = 0.0;
        }

        //Serial print results
        Serial.print("depth:");
        Serial.print(depth);
        Serial.println("mm");
      }
    }
