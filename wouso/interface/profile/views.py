from datetime import datetime
from hashlib import md5
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from wouso.core.user.models import Player, PlayerGroup, PlayerSpellDue
from wouso.core.scoring.models import History
from wouso.core.magic.models import Spell
from wouso.interface.activity.models import Activity
from wouso.interface.top.models import TopUser, GroupHistory
from wouso.interface.top.models import History as TopHistory
from wouso.core.game import get_games

@login_required
def profile(request):
    list = Activity.objects.all().order_by('-timestamp')[:10]
    return render_to_response('profile/index.html',
                              {'activity': list},
                              context_instance=RequestContext(request))

@login_required
def user_profile(request, id, page=u'1'):
    try:
        profile = Player.objects.get(id=id)
    except Player.DoesNotExist:
        raise Http404

    avatar = "http://www.gravatar.com/avatar/%s.jpg?d=monsterid"\
        % md5(profile.user.email).hexdigest()
    activity_list = Activity.objects.\
        filter(Q(user_to=id) | Q(user_from=id)).order_by('-timestamp')

    top_user = profile.get_extension(TopUser)
    top_user.topgroups = list(profile.groups.all().order_by('-gclass'))
    for g in top_user.topgroups:
        g.week_evolution = top_user.week_evolution(relative_to=g)
        g.position = TopHistory.get_user_position(top_user, relative_to=g)
    history = History.user_points(profile)
    paginator = Paginator(activity_list, 10)

    try:
        activity = paginator.page(page)
    except (EmptyPage, InvalidPage):
        activity = paginator.page(paginator.num_pages)

    profile_actions = ''
    profile_superuser_actions = ''
    for g in get_games():
        profile_actions += g.get_profile_actions(request, profile)
        profile_superuser_actions += g.get_profile_superuser_actions(request, profile)

    return render_to_response('profile/profile.html',
                              {'profile': profile,
                               'avatar': avatar,
                               'activity': activity,
                               'top': top_user,
                               'scoring': history,
                               'profile_actions': profile_actions,
                               'profile_superuser_actions': profile_superuser_actions,},
                              context_instance=RequestContext(request))

@login_required
def player_group(request, id, page=u'1'):
    group = get_object_or_404(PlayerGroup, pk=id)

    top_users = group.player_set.all().order_by('-points')
    subgroups = group.children.order_by('-points')
    if group.parent:
        sistergroups = group.parent.children.order_by('-points')
    else:
        sistergroups = PlayerGroup.objects.filter(gclass=group.gclass).order_by('-points')
    history = GroupHistory(group)

    for g in group.sisters:
        g.top = GroupHistory(g)

    activity_list = Activity.objects.\
        filter(Q(user_to__groups=group) | Q(user_from__groups=group)).order_by('-timestamp')
    paginator = Paginator(activity_list, 10)
    try:
        activity = paginator.page(page)
    except (EmptyPage, InvalidPage):
        activity = paginator.page(paginator.num_pages)

    return render_to_response('profile/group.html',
                              {'group': group,
                               'top_users': top_users,
                               'subgroups': subgroups,
                               'sistergroups': sistergroups,
                               'top': history,
                               'activity': activity,
                               },
                              context_instance=RequestContext(request))

@login_required
def groups_index(request):
    groups = PlayerGroup.objects.filter(gclass=1).order_by('name')

    return render_to_response('profile/groups.html',
                              {'groups': groups},
                              context_instance=RequestContext(request))

@login_required
def magic_cast(request, destination=None, spell=None):
    player = request.user.get_profile()
    destination = get_object_or_404(Player, pk=destination)
    due = datetime.now() # TODO fixme

    if request.method == 'POST':
        spell = get_object_or_404(Spell, pk=request.POST.get('spell', 0))
        destination.cast_spell(spell, source=player, due=due)
        return HttpResponseRedirect(reverse('wouso.interface.profile.views.user_profile', args=(destination.id,)))

    return render_to_response('profile/cast.html',
                              {'destination': destination},
                              context_instance=RequestContext(request))

@login_required
def magic_summary(request):
    """ Display a summary of spells cast by me or on me """
    player = request.user.get_profile()

    cast_spells = PlayerSpellDue.objects.filter(source=player).all()

    return render_to_response('profile/spells.html',
                              {'cast': cast_spells,
                              'player': player},
                              context_instance=RequestContext(request))
