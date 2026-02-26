Voici une **reformulation claire et structurée** de la théorie derrière ta simulation, en intégrant les principes physiques, les hypothèses, et les équations clés. Cette version est adaptée à ton contexte (membrane en latex, sphère mobile, gravité, frottement) et à ton objectif de simulation numérique.

---

## **1. Contexte physique**
### **Système étudié**
- Une **membrane en latex** (élastique, sans rigidité flexionnelle) fixée sur un cercle de rayon \( R \).
- Une **sphère centrale** (masse \( m_c \), rayon \( r_c \)) déforme la membrane par son poids \( F_c = m_c g \).
- Une **petite sphère mobile** (masse \( m_p \), rayon négligeable) se déplace sur la membrane sous l’effet de la gravité et des frottements.

### **Hypothèses**
- La membrane est **mince**, **homogène**, et se déforme axisymétriquement autour de la sphère centrale.
- La déformation est **statique** (on néglige les oscillations ou la dynamique de la membrane).
- La sphère mobile est considérée comme **ponctuelle** (pas de déformation supplémentaire).
- Les frottements sont **linéaires** (proportionnels à la vitesse).

---

## **2. Déformation de la membrane**
### **Équation de la surface**
La déformation \( z(r) \) de la membrane sous une force centrale \( F_c \) est donnée par la **solution analytique pour une membrane sous tension \( T \)** :
\[
z(r) = \frac{F_c}{2\pi T} \ln\left(\frac{R}{r}\right)
\]
où :
- \( r = \sqrt{x^2 + y^2} \) (distance radiale depuis le centre),
- \( T \) : tension de la membrane (en N/m),
- \( R \) : rayon de la membrane,
- \( F_c = m_c g \) : force exercée par la sphère centrale.

### **Gradient de la surface**
Le gradient \( \nabla z \) décrit la pente locale de la membrane :
\[
\frac{\partial z}{\partial x} = \frac{F_c}{2\pi T} \cdot \frac{-x}{r^2}, \quad
\frac{\partial z}{\partial y} = \frac{F_c}{2\pi T} \cdot \frac{-y}{r^2}
\]
Ce gradient est essentiel pour projeter la gravité le long de la surface.

---

## **3. Forces agissant sur la sphère mobile**
### **Gravité projetée**
La gravité \( \mathbf{F}_g = -m_p g \mathbf{e}_z \) est projetée sur le plan tangent à la surface. L’accélération tangentielle résultante est :
\[
\mathbf{a}_g = -g \nabla z
\]
C’est cette accélération qui guide le mouvement de la sphère mobile le long de la membrane.

### **Frottement**
Les frottements sont modélisés comme une force opposée à la vitesse, proportionnelle à un coefficient \( c \) (en s⁻¹) :
\[
\mathbf{F}_f = -c \mathbf{v}
\]
L’accélération due aux frottements est donc :
\[
\mathbf{a}_f = -\frac{c}{m_p} \mathbf{v}
\]

### **Réaction normale**
La réaction normale \( \mathbf{N} \) est perpendiculaire à la surface et **ne contribue pas** au mouvement tangent. Elle est implicitement prise en compte par la projection de la gravité le long du gradient.

---

## **4. Équations du mouvement**
### **Lois de Newton en 2D**
Le mouvement de la sphère mobile est décrit par :
\[
\frac{d^2 x}{dt^2} = -g \frac{\partial z}{\partial x} - \frac{c}{m_p} v_x
\]
\[
\frac{d^2 y}{dt^2} = -g \frac{\partial z}{\partial y} - \frac{c}{m_p} v_y
\]
où \( v_x \) et \( v_y \) sont les composantes de la vitesse.

### **Intégration numérique**
Pour simuler le mouvement, on utilise une **méthode d’intégration temporelle** (ex. : Euler ou Runge-Kutta) :
1. Calculer \( \nabla z \) à la position actuelle \( (x, y) \).
2. Mettre à jour les accélérations \( a_x \) et \( a_y \) avec les termes de gravité et de frottement.
3. Mettre à jour les vitesses et positions :
   \[
   v_x(t + \Delta t) = v_x(t) + a_x \Delta t
   \]
   \[
   x(t + \Delta t) = x(t) + v_x(t + \Delta t) \Delta t
   \]
   (et idem pour \( y \)).

---

## **5. Conditions aux limites**
- **Sortie de la membrane** : Si \( r = \sqrt{x^2 + y^2} \geq R \), la sphère quitte la surface.
- **Collision avec la sphère centrale** : Si \( r \leq r_c \), la sphère mobile entre en collision avec la sphère centrale.

---

## **6. Validation et ajustement**
- **Comparaison avec l’expérience** : Utilise tes données expérimentales (trajectoires, temps de parcours) pour ajuster :
  - La tension \( T \) (via la déformation mesurée).
  - Le coefficient de frottement \( c \).
  - Le pas de temps \( \Delta t \) pour la stabilité numérique.
- **Visualisation** : Trace les trajectoires \( (x(t), y(t)) \) et compare avec tes observations.

---

## **7. Extensions possibles**
- **Effets non linéaires** : Si la membrane s’étire beaucoup, utilise un modèle hyperélastique (ex. : Mooney-Rivlin).
- **3D** : Étends la simulation pour visualiser \( z(x, y) \) et la trajectoire en 3D.
- **Frottement non linéaire** : Remplace \( \mathbf{F}_f = -c \mathbf{v} \) par un modèle plus réaliste (ex. : frottement de Coulomb).

---

### **Résumé des équations clés**
| Grandeur               | Formule                                                                 |
|------------------------|-------------------------------------------------------------------------|
| Déformation \( z(r) \) | \( \frac{F_c}{2\pi T} \ln\left(\frac{R}{r}\right) \)                   |
| Gradient \( \nabla z \) | \( \frac{F_c}{2\pi T} \cdot \frac{-\mathbf{r}}{r^2} \)                |
| Accélération \( \mathbf{a} \) | \( -g \nabla z - \frac{c}{m_p} \mathbf{v} \)                         |
| Intégration (Euler)    | \( \mathbf{v}(t + \Delta t) = \mathbf{v}(t) + \mathbf{a} \Delta t \) |

---
### **Pourquoi ce modèle ?**
- **Simplicité** : Capture l’essentiel de la physique avec des équations analytiques.
- **Flexibilité** : Permet d’ajuster les paramètres (\( T \), \( c \)) pour coller à l’expérience.
- **Extensibilité** : Peut être enrichi (3D, frottement complexe, etc.).

Si tu veux approfondir un point (ex. : détails sur l’intégration numérique, choix de \( T \), ou visualisation), dis-le-moi ! Ton approche est déjà très rigoureuse, et ces équations devraient te permettre de reproduire fidèlement ton système physique.
