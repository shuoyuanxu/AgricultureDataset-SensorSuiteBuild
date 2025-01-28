---
tags:
  - antobot
---
>[!INFO]
>The NUC on board the Antobot needs to be powered seperately to the rest of the subsystems given the voltage range. This doc gives an overview of the changes made to incorporate it. 


# Subsystem Power Details 

![[antobot_power_fig.svg|centre]]

| Item                      | Voltage         | location / colour               | Notes                                                               |
| ------------------------- | --------------- | ------------------------------- | ------------------------------------------------------------------- |
| Battery                   | 48-52 v approx. | Lower deck (not shown)          |                                                                     |
| NUC                       | 19-24 v         | Lower deck, shown in light blue |                                                                     |
| Power Delivery Unit (PDU) | vbat            | Light pink                      | Provides power to other systems                                     |
| uCRU                      | powered by PDU  | Yellow                          | Handled by PDU, doesn't need discussion here                        |
| Jetson                    | 12 v            | Red                             | Powered by screw terminal socket. Temporarily removed (28th Jan 24) |

# Added Systems 

We have added a 13th Generation Intel NUC, which takes 19-24v and consume ~100W at full power. This can't be directly powered by any existing subsystem, so a [Meanwell SD-150C-24 24v ](https://uk.rs-online.com/web/p/dc-dc-converters/6783596)regulator has been added. The 50v line from the PDU turned out to be incompatible - so an additional [12v relay](https://www.amazon.co.uk/Heschen-Single-Phase-SSR-100DD-24-220VAC/dp/B0716S1GS8) is needed to switch the lines between the Meanwell and battery on and off. For the relay, a generic 24-220v, 100A unit has been chosen. 

The new schematic is shown below. All the additional subsystems are on the lower deck of the Antobot. 

![[power_spec_fig 1.svg|centre]]
