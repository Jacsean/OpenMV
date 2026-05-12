"""
模板创建节点 - 从轮廓生成可复用的模板数据

提供完整的模板创建功能，包括：
- 支持多种特征提取算法（Hu矩、Shape Context、Hausdorff）
- 灵活的目标轮廓选择策略（按索引/形状/面积/综合筛选）
- 模板数据序列化和标准化输出
- 模板预览图像绘制
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np
from datetime import datetime


class TemplateCreatorNode(BaseNode):
    """
    模板创建节点
    
    从轮廓分析结果中提取特征描述符并生成模板数据。
    
    功能特性：
    - 支持Hu矩、Shape Context、Hausdorff三种特征算法
    - 提供4种目标轮廓选择模式（索引/形状/面积/综合）
    - 生成标准化的JSON格式模板数据
    - 可视化预览目标轮廓
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'match_location'
    NODE_NAME = '模板创建'
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(TemplateCreatorNode, self).__init__()
        
        # 初始化Shape Context描述符缓存（LRU策略，最大100个）
        self._shape_context_cache = {}
        self._cache_max_size = 100
        
        # 输入端口
        self.add_input('统计数据', color=(255, 255, 100))
        
        # 输出端口
        self.add_output('模板数据', color=(255, 255, 100))
        self.add_output('模板预览图像', color=(100, 255, 100))
        
        # 算法选择参数
        self.add_combo_menu('algorithm', '特征算法',
                           items=['hu_moments', 'shape_context', 'hausdorff'],
                           tab='properties')
        
        # 目标选择参数
        self.add_combo_menu('selection_mode', '选择模式',
                           items=['by_index', 'by_shape', 'by_area', 'advanced'],
                           tab='properties')
        
        self.add_spinbox('target_index', '目标索引', value=0, min_value=0, max_value=100, tab='properties')
        
        self.add_combo_menu('shape_filter', '形状类型',
                           items=['circle', 'rectangle', 'line'],
                           tab='properties')
        
        self.add_spinbox('confidence_min', '最小置信度', value=0.9, min_value=0.0, max_value=1.0, double=True, tab='properties')
        
        self.add_spinbox('area_min', '最小面积', value=100, min_value=1, max_value=999999, tab='properties')
        
        self.add_spinbox('area_max', '最大面积', value=1000, min_value=1, max_value=999999, tab='properties')
        
        # Shape Context高级参数
        self.add_spinbox('n_sample_points', '轮廓点采样数', value=100, min_value=50, max_value=500, tab='properties')
        self.add_spinbox('n_radial_bins', '径向bins数量', value=4, min_value=2, max_value=10, tab='properties')
        self.add_spinbox('n_angular_bins', '角度bins数量', value=12, min_value=6, max_value=36, tab='properties')
        self.add_spinbox('inner_radius_ratio', '内半径比例', value=0.1, min_value=0.01, max_value=1.0, double=True, tab='properties')
        
        # 采样策略参数
        self.add_combo_menu('sampling_strategy', '采样策略',
                           items=['uniform', 'arc_length', 'douglas_peucker'],
                           tab='properties')
        
        # 鲁棒性增强参数
        self.add_checkbox('enable_smoothing', '启用轮廓平滑', text='', state=False, tab='properties')
        self.add_spinbox('smoothing_kernel_size', '平滑核大小', value=5, min_value=3, max_value=15, tab='properties')
        self.add_checkbox('enable_scale_normalization', '启用尺度归一化', text='', state=False, tab='properties')
    
    def _check_shape_context_availability(self):
        """
        检查Shape Context算法是否可用
        
        Returns:
            bool: 是否可用
        """
        try:
            import cv2.xfeatures2d
            return True
        except ImportError:
            self.log_warning("⚠️ Shape Context算法需要安装opencv-contrib-python")
            self.log_info("💡 安装命令: pip install opencv-contrib-python")
            return False
    
    def _generate_contour_key(self, contour):
        """
        生成轮廓的唯一键值（用于缓存）
        
        Args:
            contour: 轮廓点集
            
        Returns:
            str: 轮廓的唯一标识符
        """
        # 使用轮廓的哈希值作为键
        contour_hash = hash(contour.tobytes())
        return f"contour_{contour_hash}"
    
    def _get_cached_descriptor(self, contour_key):
        """
        从缓存中获取描述符
        
        Args:
            contour_key: 轮廓键值
            
        Returns:
            dict or None: 缓存的描述符，未命中则返回None
        """
        if contour_key in self._shape_context_cache:
            self.log_info(f"💾 缓存命中: {contour_key[:20]}...")
            return self._shape_context_cache[contour_key]
        return None
    
    def _cache_descriptor(self, contour_key, descriptor):
        """
        将描述符存入缓存（LRU策略）
        
        Args:
            contour_key: 轮廓键值
            descriptor: 描述符数据
        """
        # LRU淘汰：如果缓存已满，删除最早的条目
        if len(self._shape_context_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._shape_context_cache))
            del self._shape_context_cache[oldest_key]
            self.log_info(f"🗑️ 缓存淘汰: {oldest_key[:20]}...")
        
        self._shape_context_cache[contour_key] = descriptor
        self.log_info(f"💾 缓存保存: {contour_key[:20]}... (当前缓存大小: {len(self._shape_context_cache)})")
    
    def _clear_cache(self):
        """清空缓存"""
        cache_size = len(self._shape_context_cache)
        self._shape_context_cache.clear()
        self.log_info(f"🗑️ 缓存已清空 (释放{cache_size}个条目)")
    
    def _extract_hu_moments(self, contour):
        """
        提取Hu矩特征
        
        Args:
            contour: 轮廓点集
            
        Returns:
            dict: Hu矩特征数据
        """
        try:
            # 计算矩
            moments = cv2.moments(contour)
            
            # 计算Hu矩
            hu_moments = cv2.HuMoments(moments)
            
            # 转换为列表（Hu矩是对数尺度，可能为负数）
            hu_list = hu_moments.flatten().tolist()
            
            # 计算参考信息
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            return {
                'hu_moments': hu_list,
                'reference_area': round(area, 2),
                'reference_perimeter': round(perimeter, 2)
            }
        
        except Exception as e:
            self.log_error(f"Hu矩提取失败: {e}")
            return None
    
    def _arc_length_sampling(self, contour, target_points):
        """
        基于弧长的等距采样
        
        Args:
            contour: 轮廓点集
            target_points: 目标采样点数
            
        Returns:
            numpy.ndarray: 采样后的点集
        """
        if len(contour) <= target_points:
            return contour.reshape(-1, 2).astype(np.float32)
        
        # 计算累积弧长
        distances = np.cumsum(np.linalg.norm(np.diff(contour, axis=0), axis=1))
        total_length = distances[-1]
        
        if total_length == 0:
            return contour[:target_points].reshape(-1, 2).astype(np.float32)
        
        # 等距采样
        sample_distances = np.linspace(0, total_length, target_points)
        indices = np.searchsorted(distances, sample_distances)
        
        # 确保索引不越界
        indices = np.clip(indices, 0, len(contour) - 1)
        
        return contour[indices].reshape(-1, 2).astype(np.float32)
    
    def _douglas_peucker_sampling(self, contour, target_points):
        """
        使用Douglas-Peucker算法简化轮廓
        
        Args:
            contour: 轮廓点集
            target_points: 目标采样点数
            
        Returns:
            numpy.ndarray: 简化后的点集
        """
        if len(contour) <= target_points:
            return contour.reshape(-1, 2).astype(np.float32)
        
        # 自适应epsilon：根据轮廓周长和目标点数计算
        perimeter = cv2.arcLength(contour, True)
        epsilon = perimeter / (target_points * 2)
        
        # OpenCV内置函数
        simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        
        # 如果简化后点数仍过多，进一步增加epsilon
        while len(simplified) > target_points and epsilon < perimeter / 10:
            epsilon *= 1.2
            simplified = cv2.approxPolyDP(contour, epsilon, closed=True)
        
        return simplified.reshape(-1, 2).astype(np.float32)
    
    def _smooth_contour(self, contour, kernel_size=5):
        """
        轮廓平滑滤波
        
        Args:
            contour: 原始轮廓
            kernel_size: 滤波器大小（奇数）
            
        Returns:
            numpy.ndarray: 平滑后的轮廓
        """
        if len(contour) < kernel_size:
            return contour.copy()
        
        # 确保kernel_size为奇数
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        smoothed = np.zeros_like(contour, dtype=np.float32)
        half_kernel = kernel_size // 2
        
        # 移动平均滤波
        for i in range(len(contour)):
            indices = [(i + j) % len(contour) for j in range(-half_kernel, half_kernel + 1)]
            smoothed[i] = np.mean(contour[indices], axis=0)
        
        return smoothed.astype(np.int32)
    
    def _normalize_scale(self, contour, reference_area):
        """
        尺度归一化
        
        Args:
            contour: 候选轮廓
            reference_area: 参考面积（来自模板）
            
        Returns:
            numpy.ndarray: 归一化后的轮廓
        """
        current_area = cv2.contourArea(contour)
        
        if current_area == 0 or reference_area == 0:
            self.log_warning("⚠️ 面积为0，跳过尺度归一化")
            return contour.copy()
        
        # 计算缩放比例
        scale_factor = np.sqrt(reference_area / current_area)
        
        # 以质心为中心缩放
        moments = cv2.moments(contour)
        if moments['m00'] == 0:
            return contour.copy()
        
        cx = moments['m10'] / moments['m00']
        cy = moments['m01'] / moments['m00']
        
        normalized = (contour - np.array([cx, cy])) * scale_factor + np.array([cx, cy])
        
        return normalized.astype(np.int32)
    
    def _validate_contour(self, contour):
        """
        验证轮廓有效性
        
        Args:
            contour: 待验证轮廓
            
        Returns:
            bool: 是否有效
        """
        # 检查点数
        if len(contour) < 3:
            self.log_warning("⚠️ 轮廓点数不足 (<3)，视为无效")
            return False
        
        # 检查面积
        area = cv2.contourArea(contour)
        if area == 0:
            self.log_warning("⚠️ 轮廓面积为0，视为无效")
            return False
        
        # 检查周长
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            self.log_warning("⚠️ 轮廓周长为0，视为无效")
            return False
        
        return True
    
    def _sample_contour_points(self, contour, n_points, sampling_strategy='arc_length'):
        """
        采样轮廓点
        
        Args:
            contour: 轮廓点集
            n_points: 目标采样点数
            sampling_strategy: 采样策略 ('uniform'/'arc_length'/'douglas_peucker')
            
        Returns:
            numpy.ndarray: 采样后的点集
        """
        if len(contour) <= n_points:
            return contour.reshape(-1, 2).astype(np.float32)
        
        if sampling_strategy == 'arc_length':
            return self._arc_length_sampling(contour, n_points)
        elif sampling_strategy == 'douglas_peucker':
            return self._douglas_peucker_sampling(contour, n_points)
        else:  # uniform (默认)
            indices = np.linspace(0, len(contour) - 1, n_points, dtype=int)
            return contour[indices].reshape(-1, 2).astype(np.float32)
    
    def _extract_shape_context(self, contour, params):
        """
        提取Shape Context特征
        
        Args:
            contour: 轮廓点集
            params: 参数字典
            
        Returns:
            dict: Shape Context特征数据
        """
        try:
            # 检查依赖
            if not self._check_shape_context_availability():
                self.log_error("❌ Shape Context不可用，请安装opencv-contrib-python")
                return None
            
            import cv2.xfeatures2d
            
            # 参数配置与验证
            n_points = int(params.get('n_sample_points', 100))
            n_radial_bins = int(params.get('n_radial_bins', 4))
            n_angular_bins = int(params.get('n_angular_bins', 12))
            inner_radius_ratio = float(params.get('inner_radius_ratio', 0.1))
            sampling_strategy = params.get('sampling_strategy', 'arc_length')
            
            # 参数范围验证
            if n_points < 50 or n_points > 500:
                self.log_warning(f"⚠️ 采样点数 {n_points} 超出推荐范围 [50-500]，已自动调整")
                n_points = max(50, min(500, n_points))
            
            if n_radial_bins < 2 or n_radial_bins > 10:
                self.log_warning(f"⚠️ 径向bins {n_radial_bins} 超出推荐范围 [2-10]，已自动调整")
                n_radial_bins = max(2, min(10, n_radial_bins))
            
            if n_angular_bins < 6 or n_angular_bins > 36:
                self.log_warning(f"⚠️ 角度bins {n_angular_bins} 超出推荐范围 [6-36]，已自动调整")
                n_angular_bins = max(6, min(36, n_angular_bins))
            
            if inner_radius_ratio < 0.01 or inner_radius_ratio > 1.0:
                self.log_warning(f"⚠️ 内半径比例 {inner_radius_ratio} 超出推荐范围 [0.01-1.0]，已自动调整")
                inner_radius_ratio = max(0.01, min(1.0, inner_radius_ratio))
            
            valid_strategies = ['uniform', 'arc_length', 'douglas_peucker']
            if sampling_strategy not in valid_strategies:
                self.log_warning(f"⚠️ 未知采样策略 '{sampling_strategy}'，已切换到默认策略 'arc_length'")
                sampling_strategy = 'arc_length'
            
            # 鲁棒性增强参数
            enable_smoothing = params.get('enable_smoothing', False)
            smoothing_kernel_size = int(params.get('smoothing_kernel_size', '5'))
            enable_scale_normalization = params.get('enable_scale_normalization', False)
            
            # 验证轮廓有效性
            if not self._validate_contour(contour):
                self.log_error("❌ 轮廓无效，无法提取Shape Context特征")
                return None
            
            # 应用轮廓平滑（如果启用）
            processed_contour = contour.copy()
            if enable_smoothing:
                if smoothing_kernel_size < 3 or smoothing_kernel_size > 15:
                    self.log_warning(f"⚠️ 平滑核大小 {smoothing_kernel_size} 超出范围 [3-15]，已调整为5")
                    smoothing_kernel_size = 5
                
                processed_contour = self._smooth_contour(processed_contour, smoothing_kernel_size)
                self.log_info(f"✅ 已应用轮廓平滑 (核大小={smoothing_kernel_size})")
            
            # 记录最终使用的参数
            self.log_info(f"🔧 Shape Context参数: 点数={n_points}, 径向bins={n_radial_bins}, 角度bins={n_angular_bins}")
            self.log_info(f"   内半径={inner_radius_ratio}, 外半径=2.0, 采样策略={sampling_strategy}")
            self.log_info(f"   平滑={enable_smoothing}, 尺度归一化={enable_scale_normalization}")
            
            # 采样轮廓点（使用优化后的采样策略）
            sampled_points = self._sample_contour_points(processed_contour, n_points, sampling_strategy)
            
            self.log_info(f"✅ Shape Context采样完成 (策略={sampling_strategy}, 点数={len(sampled_points)})")
            
            # 计算参考信息
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            # 构建描述符数据
            descriptor_data = {
                'n_points': len(sampled_points),
                'inner_radius': round(inner_radius_ratio, 3),
                'outer_radius': 2.0,
                'n_radial_bins': n_radial_bins,
                'n_angular_bins': n_angular_bins,
                'sampled_points': sampled_points.tolist(),
                'sampling_strategy': sampling_strategy
            }
            
            result = {
                'shape_context_descriptor': descriptor_data,
                'reference_area': round(area, 2),
                'reference_perimeter': round(perimeter, 2)
            }
            
            # 存入缓存
            self._cache_descriptor(cache_key, result)
            
            return result
        
        except Exception as e:
            self.log_error(f"Shape Context提取失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_hausdorff(self, contour):
        """
        提取Hausdorff距离特征
        
        Args:
            contour: 轮廓点集
            
        Returns:
            dict: Hausdorff特征数据
        """
        try:
            # 创建距离提取器
            hd_extractor = cv2.createHausdorffDistanceExtractor()
            
            # 获取轮廓点集
            contour_points = contour.reshape(-1, 2).astype(np.float32)
            
            # 计算归一化因子（使用轮廓周长）
            perimeter = cv2.arcLength(contour, True)
            normalization_factor = perimeter if perimeter > 0 else 1.0
            
            # 计算参考信息
            area = cv2.contourArea(contour)
            
            return {
                'contour_points': contour_points.tolist(),
                'normalization_factor': round(normalization_factor, 2),
                'reference_area': round(area, 2),
                'reference_perimeter': round(perimeter, 2)
            }
        
        except Exception as e:
            self.log_error(f"Hausdorff特征提取失败: {e}")
            return None
    
    def _select_target_contour(self, contours):
        """
        根据配置选择目标轮廓
        
        Args:
            contours: 轮廓统计列表
            
        Returns:
            dict: 选中的轮廓数据，若无匹配则返回None
        """
        if not contours:
            self.log_error("❌ 输入轮廓列表为空")
            return None
        
        selection_mode = self.get_property('selection_mode').lower()
        
        # 模式1: 按索引选择
        if selection_mode == 'by_index':
            target_index = int(self.get_property('target_index'))
            
            if target_index < 0 or target_index >= len(contours):
                self.log_error(f"❌ 索引 {target_index} 超出范围（共{len(contours)}个轮廓）")
                return None
            
            target = contours[target_index]
            self.log_info(f"✅ 按索引选择: 第{target_index}个轮廓 (面积={target.get('area', 0):.1f})")
            return target
        
        # 模式2: 按形状类型筛选
        elif selection_mode == 'by_shape':
            shape_filter = self.get_property('shape_filter').lower()
            confidence_min = float(self.get_property('confidence_min'))
            
            candidates = [
                c for c in contours
                if c.get('shape_type', '').lower() == shape_filter
                and c.get('shape_confidence', 0) >= confidence_min
            ]
            
            if not candidates:
                self.log_error(f"❌ 未找到符合条件的{shape_filter}轮廓（置信度>={confidence_min}）")
                return None
            
            # 选择置信度最高的
            target = max(candidates, key=lambda x: x.get('shape_confidence', 0))
            self.log_info(f"✅ 按形状选择: {shape_filter} (置信度={target['shape_confidence']:.2f}, 面积={target.get('area', 0):.1f})")
            return target
        
        # 模式3: 按面积范围筛选
        elif selection_mode == 'by_area':
            area_min = float(self.get_property('area_min'))
            area_max = float(self.get_property('area_max'))
            
            candidates = [
                c for c in contours
                if area_min <= c.get('area', 0) <= area_max
            ]
            
            if not candidates:
                self.log_error(f"❌ 未找到面积在[{area_min}, {area_max}]范围内的轮廓")
                return None
            
            # 选择面积最接近中间的
            target_area = (area_min + area_max) / 2
            target = min(candidates, key=lambda x: abs(x.get('area', 0) - target_area))
            self.log_info(f"✅ 按面积选择: 面积={target['area']:.1f} (索引={target.get('index', -1)})")
            return target
        
        # 模式4: 综合筛选
        elif selection_mode == 'advanced':
            shape_filter = self.get_property('shape_filter').lower()
            confidence_min = float(self.get_property('confidence_min'))
            area_min = float(self.get_property('area_min'))
            area_max = float(self.get_property('area_max'))
            
            candidates = []
            for c in contours:
                # 形状过滤
                if shape_filter and c.get('shape_type', '').lower() != shape_filter:
                    continue
                
                # 面积过滤
                area = c.get('area', 0)
                if area < area_min or area > area_max:
                    continue
                
                # 置信度过滤
                confidence = c.get('shape_confidence', 0)
                if confidence < confidence_min:
                    continue
                
                candidates.append(c)
            
            if not candidates:
                self.log_error(f"❌ 综合筛选无匹配结果")
                self.log_info(f"   条件: 形状={shape_filter}, 面积=[{area_min},{area_max}], 置信度>={confidence_min}")
                return None
            
            # 选择置信度最高的
            target = max(candidates, key=lambda x: x.get('shape_confidence', 0))
            self.log_info(f"✅ 综合筛选: {target.get('shape_type', 'unknown')} (置信度={target['shape_confidence']:.2f})")
            return target
        
        else:
            self.log_error(f"❌ 未知的选择模式: {selection_mode}")
            return None
    
    def _create_template_data(self, contour, algorithm):
        """
        创建模板数据
        
        Args:
            contour: 轮廓点集
            algorithm: 算法名称
            
        Returns:
            dict: 模板数据字典
        """
        # 提取特征
        if algorithm == 'hu_moments':
            feature_data = self._extract_hu_moments(contour)
        elif algorithm == 'shape_context':
            params = {
                'n_sample_points': self.get_property('n_sample_points'),
                'n_radial_bins': self.get_property('n_radial_bins'),
                'n_angular_bins': self.get_property('n_angular_bins'),
                'inner_radius_ratio': self.get_property('inner_radius_ratio'),
                'sampling_strategy': self.get_property('sampling_strategy'),
                'enable_smoothing': self.get_property('enable_smoothing'),
                'smoothing_kernel_size': self.get_property('smoothing_kernel_size'),
                'enable_scale_normalization': self.get_property('enable_scale_normalization')
            }
            feature_data = self._extract_shape_context(contour, params)
        elif algorithm == 'hausdorff':
            feature_data = self._extract_hausdorff(contour)
        else:
            self.log_error(f"❌ 未知的算法: {algorithm}")
            return None
        
        if not feature_data:
            return None
        
        # 构建标准模板数据结构
        template_data = {
            'metadata': {
                'algorithm': algorithm,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            },
            'template_data': feature_data,
            'reference_info': {
                'area': feature_data.get('reference_area', 0),
                'perimeter': feature_data.get('reference_perimeter', 0)
            }
        }
        
        return template_data
    
    def _draw_preview_image(self, stats_data, target_contour_stat):
        """
        绘制模板预览图像
        
        Args:
            stats_data: 完整统计数据
            target_contour_stat: 目标轮廓统计信息
            
        Returns:
            numpy.ndarray: 预览图像
        """
        try:
            # 注意：这里需要从原始图像数据中绘制，但由于节点只接收统计数据
            # 我们创建一个示意性的空白图像
            height, width = 400, 600
            preview_image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # 添加文字说明
            cv2.putText(preview_image, "Template Preview", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 显示目标轮廓信息
            info_lines = [
                f"Index: {target_contour_stat.get('index', 'N/A')}",
                f"Area: {target_contour_stat.get('area', 0):.1f}",
                f"Shape: {target_contour_stat.get('shape_type', 'unknown')}",
                f"Confidence: {target_contour_stat.get('shape_confidence', 0):.2f}"
            ]
            
            y_offset = 80
            for line in info_lines:
                cv2.putText(preview_image, line, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                y_offset += 30
            
            # 绘制简化的轮廓示意（矩形框）
            bounding_rect = target_contour_stat.get('bounding_rect', {})
            if bounding_rect:
                x = bounding_rect.get('x', 100)
                y = bounding_rect.get('y', 100)
                w = bounding_rect.get('w', 200)
                h = bounding_rect.get('h', 150)
                
                # 缩放到预览图像尺寸
                scale = min(width / 800, height / 600)
                x_scaled = int(x * scale) + 50
                y_scaled = int(y * scale) + 50
                w_scaled = int(w * scale)
                h_scaled = int(h * scale)
                
                # 绘制目标轮廓（红色加粗）
                cv2.rectangle(preview_image, (x_scaled, y_scaled),
                             (x_scaled + w_scaled, y_scaled + h_scaled),
                             (0, 0, 255), 3)
                
                # 绘制质心
                centroid = target_contour_stat.get('centroid', {})
                if centroid:
                    cx = int(centroid.get('x', 0) * scale) + 50
                    cy = int(centroid.get('y', 0) * scale) + 50
                    cv2.circle(preview_image, (cx, cy), 8, (0, 255, 255), -1)
                    cv2.drawMarker(preview_image, (cx, cy), (255, 255, 0),
                                  markerType=cv2.MARKER_CROSS, markerSize=15, thickness=2)
            
            self.log_info("✅ 预览图像已生成")
            return preview_image
        
        except Exception as e:
            self.log_warning(f"预览图像生成失败: {e}")
            # 返回空白图像
            return np.zeros((400, 600, 3), dtype=np.uint8)
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 统计数据字典
            
        Returns:
            dict: 包含模板数据和预览图像的字典
        """
        try:
            # Step 1: 验证输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_error("❌ 未接收到统计数据输入")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            stats_data = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if not isinstance(stats_data, dict):
                self.log_error("❌ 输入数据格式错误，期望字典类型")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            # Step 2: 获取轮廓列表
            contours = stats_data.get('contours', [])
            
            if not contours:
                self.log_error("❌ 统计数据中无轮廓信息")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            self.log_info(f"📊 接收到 {len(contours)} 个轮廓的统计数据")
            
            # Step 3: 选择目标轮廓
            target_stat = self._select_target_contour(contours)
            
            if not target_stat:
                self.log_error("❌ 未能选择到目标轮廓")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            # Step 4: 获取算法配置
            algorithm = self.get_property('algorithm').lower()
            
            # 若选择Shape Context但不可用，自动降级
            if algorithm == 'shape_context' and not self._check_shape_context_availability():
                self.log_warning("⚠️ Shape Context不可用，已自动切换到Hu矩算法")
                algorithm = 'hu_moments'
            
            self.log_info(f"🔧 使用算法: {algorithm}")
            
            # Step 5: 重建轮廓点集（从边界框近似）
            # 注意：实际应用中应从原始图像重新提取轮廓，这里简化处理
            bounding_rect = target_stat.get('bounding_rect', {})
            if bounding_rect:
                x = bounding_rect.get('x', 0)
                y = bounding_rect.get('y', 0)
                w = bounding_rect.get('w', 100)
                h = bounding_rect.get('h', 100)
                
                # 创建近似轮廓（矩形）
                contour = np.array([
                    [[x, y]],
                    [[x + w, y]],
                    [[x + w, y + h]],
                    [[x, y + h]]
                ], dtype=np.int32)
            else:
                self.log_error("❌ 目标轮廓缺少边界框信息")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            # Step 6: 创建模板数据
            template_data = self._create_template_data(contour, algorithm)
            
            if not template_data:
                self.log_error("❌ 模板数据创建失败")
                return {
                    '模板数据': None,
                    '模板预览图像': None
                }
            
            # 添加来源信息
            template_data['source_info'] = {
                'index': target_stat.get('index', -1),
                'shape_type': target_stat.get('shape_type', 'unknown'),
                'shape_confidence': target_stat.get('shape_confidence', 0)
            }
            
            # Step 7: 生成预览图像
            preview_image = self._draw_preview_image(stats_data, target_stat)
            
            self.log_success(f"✅ 模板创建完成 (算法={algorithm}, 面积={target_stat.get('area', 0):.1f})")
            
            return {
                '模板数据': template_data,
                '模板预览图像': preview_image
            }
        
        except Exception as e:
            self.log_error(f"❌ 模板创建错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                '模板数据': None,
                '模板预览图像': None
            }
