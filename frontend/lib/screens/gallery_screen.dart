import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/mission_model.dart';
import 'mission_detail_screen.dart';

class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key});

  @override
  State<GalleryScreen> createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> {
  // 'desc' for 최근 날짜순, 'asc' for 오래된 날짜순
  String _sortOrder = 'desc';
  bool _isSearching = false;
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101622), // background-dark
      appBar: AppBar(
        backgroundColor: const Color(0xFF101622),
        elevation: 0,
        title: _isSearching
            ? TextField(
                controller: _searchController,
                autofocus: true,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(
                  hintText: '미션 이름 검색',
                  hintStyle: TextStyle(color: Colors.white54),
                  border: InputBorder.none,
                ),
                onChanged: (value) {
                  setState(() {
                    _searchQuery = value;
                  });
                },
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    '균열 감지 갤러리',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    '활성 미션 3개 • 이상 감지 142건',
                    style: TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            decoration: const BoxDecoration(
              color: Color(0xFF1A2332),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              icon: Icon(
                _isSearching ? Icons.close : Icons.search,
                color: Colors.white70,
              ),
              onPressed: () {
                setState(() {
                  if (_isSearching) {
                    _isSearching = false;
                    _searchQuery = '';
                    _searchController.clear();
                  } else {
                    _isSearching = true;
                  }
                });
              },
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(50),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip(
                  '최근 날짜순',
                  isSelected: _sortOrder == 'desc',
                  onTap: () {
                    setState(() {
                      _sortOrder = 'desc';
                    });
                  },
                ),
                _buildFilterChip(
                  '오래된 날짜순',
                  isSelected: _sortOrder == 'asc',
                  onTap: () {
                    setState(() {
                      _sortOrder = 'asc';
                    });
                  },
                ),
              ],
            ),
          ),
        ),
      ),
      body: FutureBuilder<List<Mission>>(
        future: ApiService.getMissions(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(
              child: Text(
                'Error: ${snapshot.error}',
                style: const TextStyle(color: Colors.red),
              ),
            );
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A2332),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white10),
                    ),
                    child: const Icon(
                      Icons.folder_off_outlined,
                      size: 48,
                      color: Colors.white24,
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    '저장된 미션이 없습니다',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '새로운 미션을 시작하여\n건물 외벽 균열을 점검해보세요.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 14,
                      height: 1.5,
                    ),
                  ),
                ],
              ),
            );
          }

          final allMissions = snapshot.data!;

          // Filter missions based on _searchQuery
          final missions = allMissions.where((mission) {
            return mission.name.toLowerCase().contains(
              _searchQuery.toLowerCase(),
            );
          }).toList();

          // If no missions match the search query
          if (missions.isEmpty && _searchQuery.isNotEmpty) {
            return Center(
              child: Text(
                '"$_searchQuery" 검색 결과가 없습니다.',
                style: const TextStyle(color: Colors.grey, fontSize: 16),
              ),
            );
          }

          // Sort missions based on _sortOrder
          missions.sort((a, b) {
            if (_sortOrder == 'desc') {
              return b.createdAt.compareTo(a.createdAt); // Newest first
            } else {
              return a.createdAt.compareTo(b.createdAt); // Oldest first
            }
          });

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: missions.length,
            itemBuilder: (context, index) {
              final mission = missions[index];
              final detections = mission.detections;

              return Card(
                color: const Color(0xFF1A2332),
                margin: const EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  leading: Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      color: Colors.black26,
                      borderRadius: BorderRadius.circular(8),
                      image:
                          (detections.isNotEmpty &&
                              detections.last.imageUrl.isNotEmpty)
                          ? DecorationImage(
                              image: NetworkImage(
                                '${ApiService.baseUrl}${detections.last.imageUrl}',
                              ),
                              fit: BoxFit.cover,
                            )
                          : null,
                    ),
                    child:
                        (detections.isEmpty || detections.last.imageUrl.isEmpty)
                        ? const Icon(Icons.broken_image, color: Colors.white24)
                        : null,
                  ),
                  title: Text(
                    mission.name,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 8),
                      Text(
                        mission.description ?? 'No description',
                        style: const TextStyle(color: Colors.grey),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${detections.length} 결함 감지됨',
                        style: TextStyle(
                          color: detections.isNotEmpty
                              ? Colors.orange
                              : Colors.green,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        mission.createdAt.toIso8601String().split('T')[0],
                        style: const TextStyle(
                          color: Colors.grey,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                  trailing: const Icon(
                    Icons.arrow_forward_ios,
                    color: Colors.grey,
                    size: 16,
                  ),
                  onTap: () async {
                    await Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) =>
                            MissionDetailScreen(mission: mission),
                      ),
                    );
                    // Force refresh when coming back
                    (context as Element).markNeedsBuild();
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildFilterChip(
    String label, {
    bool isSelected = false,
    VoidCallback? onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(right: 8),
      child: ActionChip(
        onPressed: onTap ?? () {},
        label: Text(label),
        backgroundColor: isSelected
            ? const Color(0xFF135BEC)
            : const Color(0xFF1A2332),
        labelStyle: TextStyle(color: isSelected ? Colors.white : Colors.grey),
        shape: StadiumBorder(
          side: BorderSide(
            color: isSelected ? Colors.transparent : Colors.white10,
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, String subtitle) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              width: 4,
              height: 20,
              decoration: BoxDecoration(
                color: const Color(0xFF135BEC),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        Text(
          subtitle,
          style: const TextStyle(
            color: Colors.grey,
            fontSize: 12,
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  Widget _buildImageCard(
    String imageUrl,
    String tag,
    Color tagColor,
    String location,
    String id,
  ) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A2332),
        borderRadius: BorderRadius.circular(12),
        image: DecorationImage(
          image: NetworkImage(imageUrl),
          fit: BoxFit.cover,
          colorFilter: ColorFilter.mode(
            Colors.black.withOpacity(0.2),
            BlendMode.darken,
          ),
        ),
      ),
      child: Stack(
        children: [
          Positioned(
            top: 8,
            left: 8,
            right: 8,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: tagColor.withOpacity(0.9),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Text(
                    tag,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Positioned(
            bottom: 12,
            left: 12,
            right: 12,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.gps_fixed,
                      color: Color(0xFF135BEC),
                      size: 10,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      location,
                      style: const TextStyle(
                        color: Color(0xFF135BEC),
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Text(
                  'ID: $id',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 10,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
