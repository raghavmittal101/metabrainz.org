from brainzutils.flask import CustomFlask
import os


def create_app():
    app = CustomFlask(
        import_name=__name__,
        use_flask_uuid=True,
        use_debug_toolbar=True,
    )

    # Configuration files
    app.config.from_pyfile(os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..', 'default_config.py'
    ))
    app.config.from_pyfile(os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..', 'config.py'
    ), silent=True)

    app.init_loggers(
        file_config=app.config.get('LOG_FILE'),
        email_config=app.config.get('LOG_EMAIL'),
        sentry_config=app.config.get('LOG_SENTRY'),
    )

    # Database
    from metabrainz.model import db
    db.init_app(app)

    # Redis (cache)
    from brainzutils import cache
    cache.init(**app.config['REDIS'])

    # MusicBrainz OAuth
    from metabrainz.users import login_manager, musicbrainz_login
    login_manager.init_app(app)
    musicbrainz_login.init(
        app.config['MUSICBRAINZ_BASE_URL'],
        app.config['MUSICBRAINZ_CLIENT_ID'],
        app.config['MUSICBRAINZ_CLIENT_SECRET']
    )

    # Templates
    from metabrainz.utils import reformat_datetime
    app.jinja_env.filters['datetime'] = reformat_datetime
    app.jinja_env.filters['nl2br'] = lambda val: val.replace('\n', '<br />') if val else ''

    # Error handling
    from metabrainz.errors import init_error_handlers
    init_error_handlers(app)

    # Blueprints
    from metabrainz.views import index_bp
    from metabrainz.reports.financial_reports.views import financial_reports_bp
    from metabrainz.reports.annual_reports.views import annual_reports_bp
    from metabrainz.users.views import users_bp
    from metabrainz.payments.views import payments_bp
    from metabrainz.payments.paypal.views import payments_paypal_bp
    from metabrainz.payments.wepay.views import payments_wepay_bp
    from metabrainz.payments.stripe.views import payments_stripe_bp
    from metabrainz.api.views import api_bp

    app.register_blueprint(index_bp)
    app.register_blueprint(financial_reports_bp, url_prefix='/finances')
    app.register_blueprint(annual_reports_bp, url_prefix='/reports')
    app.register_blueprint(users_bp)
    app.register_blueprint(payments_bp)
    # FIXME(roman): These URLs aren't named very correct since they receive payments
    # from organizations as well as regular donations:
    app.register_blueprint(payments_paypal_bp, url_prefix='/donations/paypal')
    app.register_blueprint(payments_wepay_bp, url_prefix='/donations/wepay')
    app.register_blueprint(payments_stripe_bp, url_prefix='/donations/stripe')
    app.register_blueprint(api_bp, url_prefix='/api')

    # ADMIN SECTION

    from flask_admin import Admin
    from metabrainz.admin.views import HomeView
    admin = Admin(app, index_view=HomeView(name='Pending users'))

    # Models
    from metabrainz.model.user import UserAdminView
    from metabrainz.model.payment import PaymentAdminView
    from metabrainz.model.tier import TierAdminView
    admin.add_view(UserAdminView(db.session, category='Users', endpoint="user_model"))
    admin.add_view(PaymentAdminView(db.session, endpoint="donation_model"))
    admin.add_view(TierAdminView(db.session, endpoint="tier_model"))

    # Custom stuff
    from metabrainz.admin.views import CommercialUsersView
    from metabrainz.admin.views import UsersView
    from metabrainz.admin.views import TokensView
    from metabrainz.admin.views import StatsView
    admin.add_view(CommercialUsersView(name='Commercial users', category='Users'))
    admin.add_view(UsersView(name='Search', category='Users'))
    admin.add_view(TokensView(name='Access tokens', category='Users'))
    admin.add_view(StatsView(name='Statistics'))

    return app
