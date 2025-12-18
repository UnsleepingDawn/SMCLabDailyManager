下面是一份**可以直接放进技术文档 / 论文方法部分 / 项目说明书**的优化问题说明。我会保持**形式化、克制、不口语化**，并且把**问题语义 ↔ 数学建模**的对应关系说清楚。

---

# 小组汇报排期与组队的联合优化问题说明

## 1. 问题描述（Problem Description）

在实验室日常管理中，需要为一组成员安排**多人小组形式的阶段性汇报**。
该问题同时涉及两个相互耦合的决策过程：

1. **小组构成（Grouping）**：将所有成员划分为若干个小组；
2. **时间安排（Scheduling）**：为每个小组分配一个可行的半天汇报时段。

该问题的难点在于：

* 成员在不同半天时段存在课程冲突；
* 汇报时段存在容量约束；
* 部分成员已经提前确定必须处于同一小组；
* 对小组规模存在明显偏好（以 3 人组为主）；
* 最后一个汇报时段仅作为兜底，不应被过度使用。

因此，该问题不能被简单拆分为“先组队、再排期”的两阶段问题，而需要对**组队与排期进行联合优化**。

---

## 2. 问题形式化（Problem Formulation）

### 2.1 集合定义

* 成员集合
  $$
  \mathcal{I} = \{1, 2, \dots, N\}
  $$

* 半天汇报时段集合
  $$
  \mathcal{P} = \{1, 2, \dots, T\}
  $$

其中 (p = T) 表示**最后一个半天时段**。

* 潜在小组集合
  $$
  \mathcal{G} = \{1, 2, \dots, G_{\max}\}
  $$

其中 $G_{\max}$ 为小组数量的上界，用于建模便利。

---

### 2.2 决策变量

#### 成员分组变量

$$
y_{i,g} \in \{0,1\}
$$

表示成员 $i$ 是否被分配到小组 $g$。

---

#### 小组排期变量

$$
x_{g,p} \in \{0,1\}
$$

表示小组 $g$ 是否被安排在半天 $p$ 汇报。

---

#### 小组激活变量

$$
z_g \in \{0,1\}
$$

表示小组 $g$ 是否被实际使用。

---

#### 小组规模指示变量

$$
s_{g,k} \in \{0,1\}, \quad k \in \{2,3,4\}
$$

表示小组 $g$ 的规模是否为 $k$。

---

#### 最后半天使用指示变量

$$
\ell_g \in \{0,1\}
$$

表示小组 $g$ 是否被安排在最后一个半天时段。

---

## 3. 约束条件（Constraints）

### 3.1 成员唯一分组约束

每位成员必须且只能属于一个小组：

$$
\sum_{g \in \mathcal{G}} y_{i,g} = 1
\quad \forall i \in \mathcal{I}
$$

---

### 3.2 小组规模一致性约束

小组规模必须为 2、3 或 4，且与激活状态一致：

$$
\sum_{k \in \{2,3,4\}} s_{g,k} = z_g
$$

$$
\sum_{i \in \mathcal{I}} y_{i,g}
= 2 s_{g,2} + 3 s_{g,3} + 4 s_{g,4}
\quad \forall g \in \mathcal{G}
$$

---

### 3.3 小组汇报时段唯一性

每个激活的小组必须且只能安排在一个半天汇报：

$$
\sum_{p \in \mathcal{P}} x_{g,p} = z_g
\quad \forall g \in \mathcal{G}
$$

---

### 3.4 汇报时段容量约束

除最后一个半天外，每个半天最多允许 $m$ 个小组汇报：

$$
\sum_{g \in \mathcal{G}} x_{g,p} \le m
\quad \forall p \in \mathcal{P},; p \neq T
$$

---

### 3.5 课程冲突约束

若成员 $i$ 在半天 $p$ 有课程冲突，则其所在小组不能安排在该半天：

$$
y_{i,g} + x_{g,p} \le 1
\quad \forall i,g,p \text{ 满足课程冲突}
$$

---

### 3.6 提前组队约束

对于提前确定必须处于同一小组的成员集合 $\mathcal{A}$，要求其分组一致：

$$
y_{i,g} = y_{j,g}
\quad \forall (i,j) \in \mathcal{A},; \forall g \in \mathcal{G}
$$

---

### 3.7 最后半天指示约束

定义小组是否使用最后一个半天：

$$
\ell_g = x_{g,T}
\quad \forall g \in \mathcal{G}
$$

---

## 4. 目标函数（Objective Function）

该问题为**偏好驱动的组合优化问题**，目标函数反映实际管理中的优先级：

1. 尽量形成 3 人小组；
2. 尽量避免 4 人小组；
3. 尽量避免使用最后一个半天。

综合上述偏好，目标函数定义为：

$$
\min
\sum_{g \in \mathcal{G}}
\left(
w_2 \cdot s_{g,2}

* w_4 \cdot s_{g,4}
* \alpha \cdot \ell_g
  \right)
$$

其中：

* $w_2 > 0$：2 人组惩罚权重；
* $w_4 \gg w_2$：4 人组惩罚权重；
* $\alpha > 0$：使用最后半天的惩罚权重。

通过合理选择权重，可实现“3人组优先、最后半天兜底”的调度策略。

---

## 5. 问题性质与求解方式

该模型为一个**0–1整数线性规划(Binary Integer Linear Programming, BILP)**问题，具有以下特性：

* 同时决定分组与排期，避免局部最优；
* 所有业务规则均以硬约束或显式目标建模；
* 可通过标准 MILP 求解器（如 CBC、Gurobi、CPLEX）直接求解。

在成员规模和时段数量适中的情况下，该模型在实际管理场景中具有良好的可解性与可扩展性。




$$
\begin{aligned}
\min \quad
& \sum_{g \in \mathcal{G}}
\left(
w_2 \, s_{g,2}
+ w_4 \, s_{g,4}
+ \alpha \, \ell_g
\right)
\\[6pt]
\text{s.t.} \quad
& \left\{
\begin{aligned}
& \sum_{g \in \mathcal{G}} y_{i,g} = 1,
&& \forall i \in \mathcal{I}
\\[4pt]
& \sum_{k \in \{2,3,4\}} s_{g,k} = z_g,
&& \forall g \in \mathcal{G}
\\
& \sum_{i \in \mathcal{I}} y_{i,g}
= 2 s_{g,2} + 3 s_{g,3} + 4 s_{g,4},
&& \forall g \in \mathcal{G}
\\[4pt]
& \sum_{p \in \mathcal{P}} x_{g,p} = z_g,
&& \forall g \in \mathcal{G}
\\[4pt]
& \sum_{g \in \mathcal{G}} x_{g,p} \le m,
&& \forall p \in \mathcal{P},\; p \neq T
\\[4pt]
& y_{i,g} + x_{g,p} \le 1,
&& \forall (i,p) \in \mathcal{C},\; \forall g \in \mathcal{G}
\\[4pt]
& y_{i,g} = y_{j,g},
&& \forall (i,j) \in \mathcal{A},\; \forall g \in \mathcal{G}
\\[4pt]
& \ell_g = x_{g,T},
&& \forall g \in \mathcal{G}
\\[4pt]
& y_{i,g},\, x_{g,p},\, z_g,\, s_{g,2},\, s_{g,3},\, s_{g,4},\, \ell_g
\in \{0,1\}
\end{aligned}
\right.
\end{aligned}
$$

---

## 6. 小结

本文将实验室小组汇报安排问题建模为一个**联合分组与排期的整数线性规划问题**，通过显式建模业务偏好与约束，实现了：

* 合理的小组规模控制；
* 课程冲突的严格避免；
* 汇报时段资源的高效利用。

该建模方式为后续引入更复杂的公平性、优先级或长期调度目标提供了统一而严谨的基础。