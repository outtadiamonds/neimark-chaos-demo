#import "style.typ": setup, title, term
#show: setup.with("en")

#title[Neimark oscillator][dynamic chaos and the correlation function]

= What the program shows

The Neimark oscillator is one of the simplest mechanical systems with #term[dynamic chaos]. Its motion is strictly deterministic: the equations contain nothing random. Nevertheless, the sequence of its velocities behaves like a random process, and its correlation function decays just as for noise.

The "Demonstration" button in the menu opens a demonstration with two tabs; the tab switch is at the top of the panel on the right.
- *"Oscillator motion"* — the motion itself: a mass on a spring, the phase trajectory, the velocity $v(t)$ as its projection, the half-period map, and two nearby trajectories showing how randomness arises from dynamic uncertainty and what a bifurcation point is.
- *"Correlation function"* — step-by-step construction of the experimental correlation function of the same velocities $y_n$ and comparison with the exact theory.

When switching to the correlation tab, $gamma$ and $h$ are passed from the motion tab (clamped to the chaos region), so both tabs show the same oscillator.

== The "Oscillator motion" tab

+ *Oscillator motion* (top strip). A mass on a spring moves along the $x$ axis; the arrow above it shows the velocity. At a kick the mass flashes red. The outlined teal square is the mass of the second, nearby trajectory; while the trajectories coincide it is hidden under the main one.
+ *Phase trajectory $(x, v)$.* An unwinding spiral is drawn as the oscillator moves (section 2). Kicks are red vertical segments on the axis $x = 0$, blue points on this axis are the velocities $y_n$. Older parts of the trajectory are lighter. The nearby trajectory is shown in teal.
+ *Velocity in time $v(t)$.* The phase plane and this plot share the velocity scale, so $v(t)$ is the projection of the phase trajectory: a purple dashed line connects the current point on the phase plane with the current point of the plot. The teal curve is the velocity of the nearby trajectory: at first it coincides with the black one, then it breaks away.
+ *Half-period map $y_n arrow.r y_(n+1)$.* The two branches of the map (section 3), the branching point $y^*$ (purple dashed line) and the observed pairs $(y_n, y_(n+1))$; the latest pair is circled in purple, the pair of the nearby trajectory in teal. The shaded square is the attractor.
+ *Two trajectories: $v_0$ and $v_0 + epsilon$.* Top: the last 40 values $y_n$ of both trajectories and the level $y^*$. Bottom: the distance $|Delta y_n|$ between them on a logarithmic scale and the line $epsilon gamma^(n\/2)$ (section 6). The caption tells after how many half-periods the trajectories split, together with the estimate $ln(1\/epsilon) \/ ln sqrt(gamma)$.

*Controls.*
- Scenarios: "Point H", "Point E" (section 8), "Normal mode" (section 4) and "No kicks" — the motion goes to infinity and the program stops the experiment.
- Sliders $gamma$, $h\/a$ and the initial velocity $v_0$ (at $t = 0$ the oscillator is at $x = 0$). The parameters may be taken outside the chaos region. Any change restarts the experiment.
- "Nearby trajectory: $epsilon$" — off, $10^(-2)$, $10^(-5)$ or $10^(-8)$. The choice starts the second trajectory from the current state with the velocity larger by $epsilon$, so the divergence experiment can be repeated at any moment.
- "Animation speed", "Run/Pause" (space), "Step π" (right arrow) — advance time by exactly half a period, "Reset", "Projection" and "Points $x = 0$" — show or hide these elements.

== The "Correlation function" tab

+ *Process.* The oscillator velocities $y_n$ at the moments it passes the equilibrium position $x = 0$, i.e. every half-period. In the "continuous $v(t)$" mode the velocity is shown as a function of time. The dashed line is the mean value.
+ *Shifted copy.* The same realization shifted by $k$ steps (by time $tau$).
+ *Overlay.* Both realizations are superimposed. For every moment the product of the deviations from the mean is shown in colour: green for a positive contribution, red for a negative one.
+ *Correlation function.* The average of these products over the whole sample divided by the variance gives the next bar. Then the shift is increased and everything repeats. The dashed line is the theoretical curve.

Two small windows are placed on the right.
- *Chaos region* — the parameter plane (section 5, Fig. 3); points H and E are marked. Parameters can be chosen with a mouse click.
- *Phase plane $(x, v)$* — the trajectory of the oscillator. The purple point moves along the spiral, and the purple mark on the process plot shows which value $y_n$ it currently corresponds to.

*Controls.*
- "$y_n$ per half-period" / "continuous $v(t)$" — choice of the process.
- "Point H", "Point E" — parameters for which the theory is exact (Markov points, section 8); "Custom" — arbitrary parameters.
- Sliders $gamma$ and $h\/a$ or a click on the parameter plane. Allowed values are limited to the chaos region.
- "Sample length $N$" — how many values the products are averaged over. The larger $N$, the closer the experiment is to the theory.
- "Run/Pause" (space), "Step" (right arrow), "Reset", "Build all".
- Mouse wheel over the plots zooms, dragging scrolls the realization. F11 toggles full screen.

= Oscillator with negative friction

An #term[oscillator] is a system that oscillates about an equilibrium position. Its state is given by the displacement $x$ and the velocity $v = dot(x)$.

In an ordinary oscillator friction removes energy and the oscillations decay. #term[Negative friction] is a force directed along the velocity: it pumps energy in, as in any generator. The equation without control is
$ dot.double(x) - 2 delta dot(x) + (1 + delta^2) x = 0, quad delta > 0. $
Substituting $x = e^(r t)$ gives $r = delta plus.minus i$, hence
$ x = A_0 e^(delta t) sin(t + phi_0). $
The factor $(1 + delta^2)$ is chosen so that the frequency equals one: the period is $2 pi$ and depends neither on the amplitude nor on $delta$. Over a period the amplitude grows by the factor
$ gamma = e^(2 pi delta) > 1, $
and over a half-period by $sqrt(gamma)$.

*The kick.* To keep the motion bounded an #term[impulse control] is introduced — an instantaneous action at separate moments of time. When the oscillator passes the equilibrium position $x = 0$ with a velocity not less than the critical value $a$, the velocity is instantly reduced by $h$:
$ dot.double(x) - 2 delta dot(x) + (1 + delta^2) x = -h thin theta(dot(x) - a) thin dot(x) thin delta(x). $
Here $theta(z)$ is the Heaviside function (zero for $z < 0$, one for $z >= 0$): it allows a kick only when $dot(x) >= a$. The delta function $delta(x)$ is non-zero only at $x = 0$. The product $dot(x) thin delta(x)$ equals the delta function in time $delta(t - t_0)$, where $t_0$ is the moment of passing zero, so it describes an instantaneous push. The factor $h$ is the size of the velocity jump. Below, velocities are measured in units of $a$.

*Dimensionless quantities.* The position $x$, velocity $v$ and time $t$ are dimensionless. Dimensional quantities are $X = L x$, $V = L omega v$, $T = t \/ omega$, where $L$ is a chosen length scale and $omega$ a frequency scale. The model does not fix their numerical values. Velocities are further measured in units of the threshold $a$, i.e. $a = 1$. One half-swing lasts exactly $pi$.

The #term[phase plane] has $x$ on the horizontal axis and $v$ on the vertical one. The state of the oscillator is a point on it, and the motion is drawn as a curve, the #term[phase trajectory]. Negative friction gives an unwinding spiral, and a kick is a vertical jump downwards on the axis $x = 0$ (Fig. 1).

#figure(image("fig_phase.png", width: 58%), caption: [Phase trajectory. The points $y_1, y_2, dots$ are the velocities at the passages of $x = 0$. Red arrows are kicks: the first one reverses the velocity, the second only reduces it.])

= Half-period map

The #term[Poincaré section] is a technique in which, instead of the whole trajectory, one considers only the points where it crosses a chosen line. Here this line is the velocity axis $x = 0$.

Let $y_n$ be the velocity right after the $n$-th passage of $x = 0$ (after the kick, if there was one). There are no kicks until the next passage, and the solution is known exactly:
$ x(u) = y_n e^(delta u) sin u, quad v(u) = y_n f(u), quad 0 <= u < pi, $
where $f(u) = e^(delta u) (delta sin u + cos u)$ is the shape of the velocity over one half-period. At $u = pi$ the oscillator passes $x = 0$ again with the velocity $-sqrt(gamma) y_n$: the velocity has changed sign and grown by the factor $sqrt(gamma)$. Taking the kick into account we obtain a #term[point map] — a rule that gives the next value from the current one:
$ y_(n+1) = -sqrt(gamma) y_n - h thin theta(-sqrt(gamma) y_n - a). $ <map>

#figure(image("fig_map.png", width: 56%), caption: [Graph of the map (@map) at point H. The shaded square is the attractor.])

The graph of the map (Fig. 2) consists of two straight lines with the slope $-sqrt(gamma)$.
- The #term[branching point] $y^* = -a \/ sqrt(gamma)$ separates them: the kick condition $-sqrt(gamma) y >= a$ is equivalent to $y <= y^*$. To the left of $y^*$ a kick happens during the half-period, to the right it does not.
- An #term[attractor] is a set that attracts trajectories and that they never leave. Here it is the interval $[-sqrt(gamma) a, a]$. The upper edge equals $a$ because anything that would end up higher is knocked down by the kick. The lower edge is the image of the upper one.

= Two modes

The mode is determined by which is larger: the kick $h$ or the threshold $a$.

*Normal mode, $h < a$.* A kick happens at a velocity not less than $a$ and removes less than $a$, so the velocity after the kick stays positive. The kick does not change the direction of motion.

*Anomalous mode, $h > a$.* A kick can remove more than the velocity was, and then the velocity after the kick is negative: the kick reverses the oscillator.

*Signs of neighbouring values.* The swing itself always changes the sign of the velocity: half a period later the oscillator passes $x = 0$ in the opposite direction. A kick is possible only at a positive velocity.
- After a positive $y_n$ the next value is always negative: the oscillator returns with a negative velocity and there is no kick.
- After a negative $y_n$ the velocity at the end of the half-period is $z = -sqrt(gamma) y_n > 0$, and three cases are possible:

#table(
  columns: (auto, auto, auto, auto),
  align: center,
  table.header[*Velocity before the kick*][*Kick*][*Velocity after*][*Sign of $y_(n+1)$*],
  [$z < a$], [no], [$z$], [$+$],
  [$a <= z < h$], [yes], [$z - h < 0$], [$-$],
  [$z >= h$], [yes], [$z - h >= 0$], [$+$],
)

The second row exists only for $h > a$. Therefore in the normal mode the signs alternate strictly, while in the anomalous mode two negative values in a row are possible (but not two positive ones). On the phase plane, after a reversing kick the trajectory stays in the half-plane $x < 0$ (Fig. 1, values $y_1$ and $y_2$).

*What the program implements.* The program is built for the anomalous mode and uses the half-period map, as in [1]. Points H and E lie in the anomalous mode. In the "Custom" mode the normal mode can be selected as well ($gamma < 2$, $h\/a < 1$). There, because of the strict alternation of signs, the half-period sequence contains a non-random component, and $R(k)$ does not decay to zero but keeps changing sign. In the normal mode the decay is observed for the map over a full period.

= Chaos region

The theory holds as long as the motion stays on the interval $[-sqrt(gamma) a, a]$. This gives two conditions on the parameters.

*The kick is not too weak.* Over a full cycle a positive velocity $y$ turns into $gamma y - h$: it grows by the factor $gamma$ and is reduced by $h$. It does not grow if $gamma y - h <= y$, i.e. $y <= h \/ (gamma - 1)$. The largest value on the attractor is $a$, hence
$ h\/a >= gamma - 1. $
Otherwise the pumping is stronger than the kicks and the motion goes to infinity. On the "Oscillator motion" tab this is seen in the "No kicks" scenario ($h = 0$): the spiral unwinds without bound, and the program stops the experiment when the velocity exceeds $10^4$.

*The kick is not too strong.* The lowest value after a kick is $a - h$. It must not fall below the lower edge:
$ a - h >= -sqrt(gamma) a, quad "i.e." quad h\/a <= 1 + sqrt(gamma). $

Together with the condition $gamma > 1$ these inequalities single out the #term[chaos region] $A B C$ on the #term[parameter plane] $(h\/a, gamma)$ (Fig. 3).

#figure(image("fig_plane.png", width: 52%), caption: [Parameter plane. The blue and beige areas together form the chaos region; the beige one is the normal mode.])

The lines on the plane correspond to special coincidences.

#table(
  columns: (auto, auto, 1fr),
  table.header[*Line*][*Equation*][*Meaning*],
  [$A B$], [$h\/a = gamma - 1$], [the lower edge is mapped into the upper edge],
  [$C B$], [$h\/a = 1 + sqrt(gamma)$], [the branching point after a kick lands on the lower edge],
  [$A C$], [$gamma = 1$], [no pumping and no chaos],
  [$G D$], [$h\/a = 1$], [boundary of the modes: normal on the left, anomalous on the right],
  [$H C$], [$h\/a = 1 + 1\/sqrt(gamma)$], [the branching point after a kick is mapped into itself],
  [$D E$], [$h\/a = gamma$], [the lower edge is mapped into zero],
)

Points H, E and G lie at intersections of these lines: $H = A B inter H C$, $E = D E inter C B$, $G = A B inter G D$.

= Where randomness comes from

#term[Dynamic chaos] is irregular, random-looking behaviour of a system whose equations contain no random quantities.

*Instability.* The map (@map) stretches everywhere: the distance between close points grows by the factor $sqrt(gamma) > 1$ per half-period, and by $(sqrt(gamma))^n$ over $n$ half-periods. The rate of this divergence is measured by the #term[Lyapunov exponent]; here it equals $ln sqrt(gamma) = pi delta$ per half-period. An initial uncertainty $epsilon$ grows to the size of the attractor in about $ln(1\/epsilon) \/ ln sqrt(gamma)$ steps. The initial state is always known with finite accuracy, so a long-term forecast is impossible — this is #term[dynamic uncertainty].

*Bifurcation point.* A #term[bifurcation] is a qualitative change of behaviour under a small change of a quantity. The threshold $a$ is a bifurcation point in the space of velocities: a slightly smaller velocity passes without a kick, a slightly larger one gets a kick. On the map it corresponds to the branching point: two arbitrarily close points on different sides of $y^*$ are separated by $h$ already at the next step.

*How it is seen in the program.* On the "Oscillator motion" tab a second trajectory runs next to the main one, started with the velocity larger by $epsilon$. While both velocities are on the same side of $y^*$, they go through the same branch of the map, and the difference between them grows exactly as $epsilon gamma^(n\/2)$ — a straight line on the logarithmic plot. When the difference becomes comparable with the distance to $y^*$, one trajectory gets a kick and the other does not: they land on different branches and from then on move independently. This is the mechanism by which randomness appears: the exponential instability brings an arbitrarily small uncertainty up to the bifurcation point, and there the uncertainty turns into a "choice" between two outcomes. Making $epsilon$ a thousand times smaller only slightly delays the divergence:

#table(
  columns: (auto, auto, auto),
  table.header[$epsilon$][estimate $ln(1\/epsilon) \/ ln sqrt(gamma)$][divergence in the program, point H],
  [$10^(-2)$], [9.6], [12],
  [$10^(-5)$], [23.9], [25],
  [$10^(-8)$], [38.3], [40],
)

*Strange attractor.* Stretching drives trajectories apart, while the kick returns them to a bounded interval. An attractor on which the motion is unstable is called #term[strange]; the system considered is one of the simplest examples.

*Mixing and ergodicity.* #term[Mixing] is the property of a system to "forget" its initial condition: any small set of initial states eventually spreads uniformly over the attractor. #term[Ergodicity] is a weaker property: one long trajectory visits all parts of the attractor, so the time average equals the ensemble average. Because of mixing the behaviour of a deterministic system becomes indistinguishable from random.

= Correlation function

Since an individual trajectory cannot be predicted, the process is described statistically. A process is called #term[stationary] if its statistical properties do not change with time. The #term[stationary probability density] $w(y)$ shows how often values near $y$ occur.

The #term[correlation function] shows how strongly the value at a given moment is related to the value $k$ steps later:
$ R(k) = lr(⟨ (y_n - ⟨y⟩)(y_(n+k) - ⟨y⟩) ⟩), quad rho(k) = R(k) \/ R(0). $
The quantity $R(0)$ is the variance. For an ergodic process the ensemble average may be replaced by the time average along one long realization. This is exactly how the program builds the experimental function:
$ hat(R)(k) = 1/(N-k) sum_(n=1)^(N-k) (y_n - overline(y))(y_(n+k) - overline(y)). $
The error of this estimate is of the order of $1 \/ sqrt(N)$.

*Visual meaning.* The realization is copied and shifted by $k$, then laid over the original, and the deviations are multiplied at every point.
- If the copy "resembles" the original, the products are mostly positive and $R(k) > 0$.
- If the copy is "in antiphase", the products are mostly negative.
- If the values separated by the shift $k$ are no longer related, positive and negative contributions cancel and $R(k) approx 0$.

The shift at which the correlation practically vanishes is called the #term[correlation time]. For the Neimark oscillator it is finite even though the process is strictly deterministic: this is a consequence of mixing. The larger $sqrt(gamma)$, the faster the correlation decays.

= Exact theory: Markov partition

A process is called #term[Markov] if its future depends only on its current state.

The images of the upper edge $a$, of the point $a - h$ (where the branching point goes after a kick) and of the lower edge, together with the branching point, divide the attractor into intervals. Every half-period new partition points appear. If from some step on no new points appear, we obtain a #term[Markov partition]: each interval $I_alpha$ is mapped linearly and entirely onto a union of several intervals:
$ I_alpha -> union.big_beta d_(alpha beta) I_beta, quad y -> s_alpha y + C_alpha, quad d_(alpha beta) in {0, 1}. $
The matrix $D = ||d_(alpha beta)||$ is the transition matrix. Transitions between the intervals form a Markov chain, and the continuous deterministic process turns out to be exactly equivalent to a discrete Markov process. Parameter values for which the partition is finite are called #term[Markov points].

The #term[Perron–Frobenius operator] $P$ carries a probability density one step forward:
$ (P rho)(z) = sum_(y: thin T(y) = z) rho(y) \/ |T'(y)|. $
The meaning of the formula: if an interval is stretched by the factor $sqrt(gamma)$, the density on it decreases by the factor $sqrt(gamma)$. The stationary density is piecewise constant: $w(y) = w_alpha$ for $y in I_alpha$. Its values follow from
$ w_beta = sum_alpha d_(alpha beta) w_alpha \/ |s_alpha|, quad sum_alpha w_alpha |I_alpha| = 1. $
The correlation function is expressed through the same operator:
$ lr(⟨ y_0 y_k ⟩) = integral z thin (P^k [y thin w(y)])(z) thin d z. $
The operator $P$ maps functions that are linear on every interval into functions of the same kind. Therefore the calculation reduces to finite recurrence relations for two coefficients per interval. This is equivalent to the recursion for the integrals $U_alpha [k]$, $V_alpha [k]$ in [1].

Markov points are dense everywhere on the parameter plane. For arbitrary parameters the program builds an _approximate_ Markov partition: new points closer than a given accuracy to existing ones are merged with them. The quality of the approximation can be judged by how well the theoretical curve matches the experiment.

*Point H:* $sqrt(gamma) = (1 + sqrt(5))\/2 approx 1.618$, $h\/a = gamma - 1 approx 1.618$. The partition has two intervals: $I_1 = [-a\/sqrt(gamma), a]$ of length $sqrt(gamma) a$ and $I_2 = [-sqrt(gamma) a, -a\/sqrt(gamma)]$ of length $a$. The interval $I_1$ lies to the right of the branching point and is mapped without a kick onto $I_1 union I_2$; the interval $I_2$ gets a kick and is mapped onto $I_1$. From the balance $w_2 = w_1 \/ sqrt(gamma)$ and the normalization we get
$ w_1 = sqrt(gamma)\/(1 + gamma) approx 0.447, quad w_2 = 1\/(1 + gamma) approx 0.276, $
and $rho(1) approx -0.809$, $rho(2) approx 0.573$, $rho(3) approx -0.382$. Asymptotically $rho(k) prop (-1\/sqrt(gamma))^k$: the correlation decays exponentially while changing sign.

*Point E:* $gamma = h\/a approx 2.618$. The lower edge is mapped into zero, and zero is a fixed point of the map. Zero becomes a new partition point, $N = 3$. Here $rho(1) approx rho(2) approx -0.118$, $rho(3) approx 0.146$.

*Point G:* $gamma = 2$, $h\/a = 1$ — on the boundary of the modes. The half-period process is non-ergodic here, and the correlation function does not tend to zero; the decay is observed for the map over a full period. In the program this point is marked on the parameter plane but has no separate button.

= Continuous process $v(t)$

In the "continuous $v(t)$" mode the velocity is considered at all moments of time, not only at the passages of $x = 0$:
$ v(t) = y_n f(t - n pi) quad "for" quad n pi <= t < (n + 1) pi. $
Every half-period is the same curve $f$ multiplied by its own value $y_n$.

*What is seen on the screen.* Time is measured in units of $pi$: one division is one half-period. The curve $v(t)$ looks like a growing sinusoid with vertical drops at the moments of kicks. The shift $tau$ changes in steps of $pi\/8$. The third plot shades the area under the product of deviations, and the fourth one builds
$ C(tau) = lr(⟨ (v(t) - ⟨v⟩)(v(t + tau) - ⟨v⟩) ⟩). $

*Theory.* For a stationary process the phase within a half-period is uniformly distributed, so for $tau = m pi + r$, $0 <= r < pi$:
$ lr(⟨ v(t) v(t + tau) ⟩) &= 1/pi M_m integral_0^(pi - r) f(u) f(u + r) d u \
  &+ 1/pi M_(m+1) integral_(pi - r)^pi f(u) f(u + r - pi) d u, $
where $M_m = lr(⟨ y_n y_(n+m) ⟩)$ are the moments of the sequence $y_n$ from section 8. The two terms correspond to two cases: the moment $t + tau$ falls into the half-period number $n + m$ or into the next one.

*How to read the result.* $C(tau)$ is a wave with a period of about $2 pi$: at $tau approx pi$ it is negative (half a period later the velocity points the opposite way), at $tau approx 2 pi$ it is positive. The amplitude of the wave first decreases — this part is determined by $R(k)$.

*Why $C(tau)$ does not decay to zero.* The oscillation period does not depend on the amplitude and the kick is instantaneous, so the zero crossings are strictly periodic; only the amplitudes are random. Such a process is called #term[cyclostationary]: its statistics are not constant but repeat with a period. The mean $⟨y⟩$ is not zero because kicks happen only when moving in one direction. Therefore $v(t)$ has a non-random periodic component $⟨y⟩ f(u)$, and $C(tau)$ contains a non-decaying periodic part proportional to $⟨y⟩^2$. The sequence $y_n$ forgets the past completely, whereas the continuous velocity forgets the amplitude but keeps the phase of the oscillations.

= Glossary

#table(
  columns: (auto, 1fr),
  table.header[*Term*][*Definition*],
  [Oscillator], [a system oscillating about an equilibrium position],
  [Negative friction], [a force along the velocity that pumps energy in],
  [$gamma$], [amplitude growth per period, $gamma = e^(2 pi delta)$],
  [Impulse control], [an instantaneous action at separate moments of time (a kick)],
  [Phase plane], [the "position — velocity" plane],
  [Phase trajectory], [the curve traced by the state on the phase plane],
  [Poincaré section], [the points where the trajectory crosses a chosen line],
  [Point map], [the rule $y_(n+1) = T(y_n)$],
  [Attractor], [a set that attracts trajectories],
  [Strange attractor], [an attractor on which the motion is unstable],
  [Branching point], [$y^* = -a\/sqrt(gamma)$: a kick to the left of it, none to the right],
  [Bifurcation], [a qualitative change of behaviour under a small change of a quantity],
  [Normal and anomalous modes], [$h < a$ and $h > a$: a kick cannot or can reverse the velocity],
  [Chaos region], [parameters for which the motion stays on the attractor],
  [Dynamic chaos], [random-looking behaviour of a deterministic system],
  [Lyapunov exponent], [the rate of divergence of close trajectories, here $ln sqrt(gamma)$],
  [Mixing], [forgetting the initial condition],
  [Ergodicity], [equality of the time average and the ensemble average],
  [Stationary process], [a process with time-independent statistics],
  [Correlation function], [a measure of the relation between values separated by a shift],
  [Correlation time], [the shift after which the relation vanishes],
  [Markov process], [a process whose future depends only on the present],
  [Markov partition], [a division of the attractor into intervals mapped entirely onto one another],
  [Markov point], [parameters for which such a partition is finite],
  [Perron–Frobenius operator], [the rule that carries a probability density one step forward],
  [Cyclostationary process], [a process with statistics periodic in time],
)

= References

+ Stratonovich R. L., Ruzmaikina A. A., Chichigina O. A. Dynamic chaos in an oscillator with negative friction. Anomalous mode \/\/ Radiophysics and Quantum Electronics. 1993. Vol. 36, No. 9. P. 613–622.
+ Neimark Yu. I. Dynamical Systems and Controlled Processes. Moscow: Nauka, 1978 (in Russian).
+ Neimark Yu. I., Landa P. S. Stochastic and Chaotic Oscillations. Moscow: Nauka, 1987 (in Russian).
+ Landa P. S., Stratonovich R. L. Stationary probability distribution for a simplest strange attractor \/\/ Dokl. Akad. Nauk SSSR. 1982. Vol. 267, No. 4.
+ Chichigina O. A. Fluctuation Processes. Lecture notes. Sec. 8.3 "Neimark oscillator", pp. 75–76 (in Russian).
